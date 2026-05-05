# The Joy of Movement – Content Creator

A Flask web application that generates authentic, brand-aligned content using AI. Built for "The Joy of Movement" – a community-focused fitness brand targeting adults 55+.

## Overview

The Content Creator helps you generate content that aligns with your brand voice, constraints, and messaging. It walks you through a 5-step workflow from brief definition to content refinement and export.

**Pipeline:** Document → Monitor → Brief → Publish → Iterate

## Features

- **5-Step Workflow:**
  1. **Prepare** – View knowledge base status (primary docs, secondary research, token count)
  2. **Brief** – Define content parameters (topic, format, template, key message)
  3. **Create** – Generate content via AI with real-time feedback
  4. **Refine** – Iterate with feedback or export directly
  5. **Done** – Success screen with export options

- **Content Formats:**
  - Blog Posts
  - Social Media Posts
  - Newsletters

- **Knowledge Base Modes:**
  - Brand Only – Use primary documents exclusively
  - Market Context Only – Use secondary research exclusively
  - Hybrid (Recommended) – Combine both for maximum differentiation

- **Export Options:**
  - Copy to Clipboard – Copy formatted content to clipboard
  - Download as TXT – Download as plain text file with date-stamped filename

## Tech Stack

- **Backend:** Flask (Python)
- **AI:** Anthropic Claude API (Haiku model for cost-efficiency)
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Session Management:** Flask sessions (per-user pipeline instances)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/miraraab/the-joy-of-movement-content-creator.git
cd the-joy-of-movement-content-creator
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements-web.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_api_key_here
```

### 5. Prepare Knowledge Base
The app expects a `knowledge_base/` directory with:
- `primary/` – Brand documents (PDFs, TXTs)
- `secondary/` – Market research documents (PDFs, TXTs)

Example structure:
```
knowledge_base/
├── primary/
│   ├── brand_guidelines.txt
│   ├── voice_and_tone.txt
│   └── company_story.txt
└── secondary/
    ├── fitness_trends.txt
    └── competitor_analysis.txt
```

## Running the Application

### Start the Server
```bash
python app.py
```

The app will start on **http://localhost:5001**

### Access the Web Interface
Open your browser and navigate to `http://localhost:5001`

## Usage

1. **Step 1 - Prepare:** Review your knowledge base stats
2. **Step 2 - Brief:** Fill in the form:
   - **Topic:** What content do you want to create?
   - **Format:** Blog, Social Media, or Newsletter
   - **Template:** Brand Only, Market Context Only, or Hybrid
   - **Key Message:** (Optional) Main point you want to emphasize
   - **Notes:** (Optional) Special instructions
3. **Step 3 - Create:** Wait for content generation
4. **Step 4 - Refine:**
   - Review generated content
   - Export immediately (Copy/Download) or
   - Provide feedback to refine further (iterate)
5. **Step 5 - Done:** Success screen with final export options

## Project Structure

```
├── app.py                    # Flask application & API routes
├── requirements-web.txt      # Python dependencies
├── templates/
│   └── index.html           # Web interface (5-step workflow)
├── static/
│   ├── style.css            # Styling (warm palette for 55+ audience)
│   └── script.js            # Frontend logic & interactions
├── src/
│   ├── content_pipeline.py  # Core pipeline stages
│   ├── prompt_templates.py  # LLM prompt templates
│   ├── document_processor.py # Document loading & processing
│   ├── llm_integration.py   # Anthropic Claude integration
│   └── knowledge_base_manager.py
├── knowledge_base/          # Brand & market research documents
│   ├── primary/
│   └── secondary/
└── output/                  # Generated content exports (auto-created)
```

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Render web interface |
| GET | `/api/pipeline-status` | Get KB stats (docs, tokens) |
| POST | `/api/brief` | Create brief & define parameters |
| POST | `/api/publish` | Generate content from brief |
| POST | `/api/iterate` | Refine content with feedback |

## Configuration

### Flask Settings
- **Port:** 5001 (configurable in `app.py`)
- **Debug Mode:** Enabled by default
- **Session Secret:** Set in `app.py` (change in production)

### Model Selection
The pipeline uses Claude **Haiku 4.5** (cost-optimized). To change:
1. Edit `src/llm_integration.py`
2. Update the `model` parameter in the API client initialization

## Design Philosophy

**Target Audience:** Adults 55+ seeking community and movement

**Design Principles:**
- Warm color palette (terracotta, gold, brown)
- Eye-level, conversational tone
- Clear, progressive workflow
- No jargon or complexity

**Brand Constraints:**
The pipeline enforces NEVER patterns:
- Seniors, anti-aging, optimize, journey, embrace
- Best years, incredible benefits, generic CTAs
- Patronizing or pity tone
- Medical/clinical framing

## Troubleshooting

### Port Already in Use
If port 5001 is occupied, change it in `app.py`:
```python
app.run(debug=True, port=5002)  # Use 5002 or another port
```

### Knowledge Base Not Found
Ensure the `knowledge_base/` directory exists with `primary/` and `secondary/` subdirectories.

### API Key Error
Check that your `.env` file contains a valid `ANTHROPIC_API_KEY`.

## Future Enhancements

- [ ] Bulk content generation
- [ ] Content performance analytics
- [ ] Scheduled publishing
- [ ] Multi-language support
- [ ] A/B testing framework
- [ ] Team collaboration features

## License

Proprietary – The Joy of Movement

## Support

For issues or feature requests, contact the development team.
