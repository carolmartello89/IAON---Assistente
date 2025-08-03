#!/usr/bin/env python3
import html.parser
import traceback

class HTMLChecker(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.errors = []
    
    def error(self, message):
        self.errors.append(message)

def check_html_file(filename):
    try:
        checker = HTMLChecker()
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        checker.feed(content)
        
        if checker.errors:
            print(f"❌ Erros em {filename}:")
            for error in checker.errors:
                print(f"  - {error}")
        else:
            print(f"✅ {filename} - HTML válido")
            
    except Exception as e:
        print(f"⚠️ Erro ao verificar {filename}: {e}")

# Verificar arquivos HTML
html_files = ['static/index.html', 'static/viral.html']

for html_file in html_files:
    check_html_file(html_file)
