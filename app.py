"""
Flask Web App for Joy of Movement Content Creator
Pipeline: Document → Monitor → Brief → Publish → Iterate
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, render_template, request, jsonify, session
from content_pipeline import ContentPipeline
from prompt_templates import ContentType, TemplateType

app = Flask(__name__)
app.secret_key = 'joy-of-movement-secret-2025'

# Pipeline instances per session
pipelines = {}

def get_or_create_session_id():
    """Get existing session ID or create new one"""
    if 'session_id' not in session:
        session['session_id'] = str(datetime.now().timestamp())
    return session['session_id']

def get_pipeline(session_id):
    """Get or create pipeline for this session"""
    if session_id not in pipelines:
        pipeline = ContentPipeline(kb_root='knowledge_base')
        pipeline.stage_document()
        pipeline.stage_monitor()
        pipelines[session_id] = {
            'pipeline': pipeline,
            'current_output': None,
            'brief': None,
        }
    return pipelines[session_id]


@app.route('/')
def index():
    """Home page"""
    get_or_create_session_id()
    return render_template('index.html')


@app.route('/api/pipeline-status', methods=['GET'])
def pipeline_status():
    """Get current pipeline status"""
    session_id = get_or_create_session_id()
    session_data = get_pipeline(session_id)
    pipeline = session_data['pipeline']

    return jsonify({
        'primary_docs': len(pipeline.kb.primary),
        'secondary_docs': len(pipeline.kb.secondary),
        'total_tokens': pipeline.processor.estimate_tokens(
            pipeline.primary_context + pipeline.secondary_context
        ),
    })


@app.route('/api/brief', methods=['POST'])
def create_brief():
    """STAGE 3: Create brief"""
    data = request.json
    session_id = get_or_create_session_id()
    session_data = get_pipeline(session_id)
    pipeline = session_data['pipeline']

    # Map format to ContentType
    format_map = {
        'blog': ContentType.BLOG_POST,
        'social': ContentType.SOCIAL_MEDIA,
        'newsletter': ContentType.NEWSLETTER,
    }

    # Map template to TemplateType
    template_map = {
        'brand': TemplateType.BRAND,
        'industry': TemplateType.INDUSTRY,
        'hybrid': TemplateType.HYBRID,
    }

    # Map format to desired_versions (only generate selected format)
    version_map = {
        'blog': ['blog_post'],
        'social': ['social_media'],
        'newsletter': ['newsletter'],
    }

    brief = pipeline.stage_brief(
        topic=data['topic'],
        content_type=format_map[data['format']],
        template_type=template_map[data['template']],
        key_message=data.get('key_message', ''),
        notes=data.get('notes', ''),
        desired_versions=version_map[data['format']],
    )

    session_data['brief'] = brief

    return jsonify({'status': 'ok', 'message': 'Brief created'})


@app.route('/api/publish', methods=['POST'])
def publish():
    """STAGE 4: Publish (generate content)"""
    session_id = get_or_create_session_id()
    session_data = get_pipeline(session_id)
    pipeline = session_data['pipeline']
    brief = session_data['brief']

    if brief is None:
        return jsonify({'error': 'No brief created'}), 400

    output = pipeline.stage_publish(brief)

    # Score the generated content
    output = pipeline.stage_score(output)

    session_data['current_output'] = output

    score_data = None
    if output.score:
        score_data = {
            'voice_authenticity': output.score.voice_authenticity,
            'constraint_compliance': output.score.constraint_compliance,
            'identity_clarity': output.score.identity_clarity,
            'story_quality': output.score.story_quality,
            'competitor_contrast': output.score.competitor_contrast,
            'overall_score': output.score.overall_score,
            'feedback': output.score.feedback,
            'issues': [{'problem': issue.problem, 'suggestion': issue.suggestion} for issue in output.score.issues],
        }

    return jsonify({
        'status': 'ok',
        'content': output.generated_text,
        'char_count': output.char_count,
        'iteration': output.iteration,
        'score': score_data,
    })


@app.route('/api/iterate', methods=['POST'])
def iterate():
    """STAGE 5: Iterate (refine with feedback)"""
    data = request.json
    session_id = get_or_create_session_id()
    session_data = get_pipeline(session_id)
    pipeline = session_data['pipeline']
    previous = session_data['current_output']

    if previous is None:
        return jsonify({'error': 'No content to iterate'}), 400

    output = pipeline.stage_iterate(previous, data['feedback'])

    # Score the refined content
    output = pipeline.stage_score(output)

    session_data['current_output'] = output

    score_data = None
    if output.score:
        score_data = {
            'voice_authenticity': output.score.voice_authenticity,
            'constraint_compliance': output.score.constraint_compliance,
            'identity_clarity': output.score.identity_clarity,
            'story_quality': output.score.story_quality,
            'competitor_contrast': output.score.competitor_contrast,
            'overall_score': output.score.overall_score,
            'feedback': output.score.feedback,
            'issues': [{'problem': issue.problem, 'suggestion': issue.suggestion} for issue in output.score.issues],
        }

    return jsonify({
        'status': 'ok',
        'content': output.generated_text,
        'char_count': output.char_count,
        'iteration': output.iteration,
        'score': score_data,
    })


@app.route('/api/export-html', methods=['POST'])
def export_html():
    """Export content as HTML"""
    session_id = get_or_create_session_id()
    session_data = get_pipeline(session_id)
    pipeline = session_data['pipeline']
    output = session_data['current_output']

    if output is None:
        return jsonify({'error': 'No content to export'}), 400

    html_path = pipeline.export_html(output)

    return jsonify({
        'status': 'ok',
        'html_path': html_path,
        'message': f'Exported to {html_path}',
    })


@app.route('/api/save-text', methods=['POST'])
def save_text():
    """Save content as text file"""
    data = request.json
    session_id = get_or_create_session_id()
    session_data = get_pipeline(session_id)
    output = session_data['current_output']

    if output is None:
        return jsonify({'error': 'No content to save'}), 400

    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_topic = ''.join(c if c.isalnum() else '_' for c in data['topic'][:30])
    filename = output_dir / f"{timestamp}_{output.content_type}_{safe_topic}.txt"

    filename.write_text(output.generated_text, encoding='utf-8')

    return jsonify({
        'status': 'ok',
        'path': str(filename),
    })


if __name__ == '__main__':
    app.run(debug=True, port=5001)
