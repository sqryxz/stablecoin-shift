import pdfkit

# Configuration for wkhtmltopdf
options = {
    'page-size': 'A4',
    'margin-top': '0.75in',
    'margin-right': '0.75in',
    'margin-bottom': '0.75in',
    'margin-left': '0.75in',
    'encoding': "UTF-8",
    'custom-header': [
        ('Accept-Encoding', 'gzip')
    ],
    'no-outline': None
}

try:
    # Convert HTML to PDF
    pdfkit.from_file('stablecoin_report.html', 'stablecoin_report.pdf', options=options)
    print("PDF generated successfully!")
except Exception as e:
    print(f"Error generating PDF: {str(e)}")
    print("Please install wkhtmltopdf using: brew install wkhtmltopdf") 