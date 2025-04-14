import markdown
from weasyprint import HTML
import tempfile

# Read the markdown file
with open('stablecoin_report.md', 'r') as f:
    markdown_content = f.read()

# Convert markdown to HTML
html_content = markdown.markdown(markdown_content)

# Add some basic CSS for better formatting
html_with_style = f"""
<html>
<head>
<style>
    body {{ font-family: Arial, sans-serif; margin: 40px; }}
    h1 {{ color: #2c3e50; }}
    h2 {{ color: #34495e; margin-top: 30px; }}
    h3 {{ color: #34495e; }}
    li {{ margin: 5px 0; }}
    code {{ background-color: #f7f9fa; padding: 2px 5px; border-radius: 3px; }}
</style>
</head>
<body>
{html_content}
</body>
</html>
"""

# Create a temporary HTML file
with tempfile.NamedTemporaryFile(suffix='.html', mode='w', encoding='utf-8') as temp:
    temp.write(html_with_style)
    temp.flush()
    
    # Convert HTML to PDF
    HTML(temp.name).write_pdf('stablecoin_report.pdf') 