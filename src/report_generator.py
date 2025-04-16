import os
import json
from datetime import datetime

class ReportGenerator:
    """Generate comprehensive HTML reports with interactive features"""
    
    # Chart configuration constants
    CHART_COLORS = {
        'success': '#28a745',
        'error': '#dc3545'
    }
    LANGUAGES = ['en', 'kh', 'cn']
    LANGUAGE_LABELS = ['English', 'Khmer', 'Chinese']

    def __init__(self, results, config):
        self.results = results
        self.config = config
        self.report_file = None
        self.matched_data = self._get_language_data('matched')
        self.mismatched_data = self._get_language_data('mismatched')

    def _get_language_data(self, data_type):
        """Get data for all languages of specified type (matched/mismatched)"""
        return [self.results.get(f"{lang}_{data_type}", 0) for lang in self.LANGUAGES]

    def _get_chart_config(self):
        """Generate Chart.js configuration"""
        return {
            'type': 'bar',
            'data': {
                'labels': self.LANGUAGE_LABELS,
                'datasets': [
                    {
                        'label': 'Matches',
                        'data': self.matched_data,
                        'backgroundColor': self.CHART_COLORS['success']
                    },
                    {
                        'label': 'Mismatches',
                        'data': self.mismatched_data,
                        'backgroundColor': self.CHART_COLORS['error']
                    }
                ]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'tooltip': {
                        'mode': 'index',
                        'intersect': False
                    }
                },
                'scales': {
                    'x': {
                        'stacked': True,
                        'title': {
                            'display': True,
                            'text': 'Languages'
                        }
                    },
                    'y': {
                        'stacked': True,
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': 'Number of Elements'
                        }
                    }
                }
            }
        }

    def generate(self):
        """Generate a detailed HTML report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = self.config.get("report_dir", "reports")
        
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
            
        self.report_file = os.path.join(report_dir, f"translation_test_report_{timestamp}.html")
        
        # Calculate statistics
        total_checks = self.results["total_elements"] * 3  # 3 languages
        total_matches = sum([self.results.get(f"{lang}_matched", 0) for lang in ["en", "kh", "cn"]])
        total_mismatches = sum([self.results.get(f"{lang}_mismatched", 0) for lang in ["en", "kh", "cn"]])
        
        match_percentage = (total_matches / total_checks) * 100 if total_checks > 0 else 0
        
        # Generate HTML with interactive features
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Translation Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; color: #333; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stats {{ display: flex; flex-wrap: wrap; gap: 20px; margin: 20px 0; }}
                .stat-card {{ flex: 1; min-width: 200px; background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stat-value {{ font-size: 24px; font-weight: bold; margin: 10px 0; }}
                .success {{ color: #28a745; }}
                .warning {{ color: #ffc107; }}
                .error {{ color: #dc3545; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; }}
                tr:nth-child(even) {{ background-color: #f8f9fa; }}
                tr:hover {{ background-color: #f1f1f1; }}
                .filter-controls {{ margin-bottom: 20px; }}
                .search {{ padding: 8px; width: 300px; margin-right: 10px; border: 1px solid #ddd; border-radius: 4px; }}
                .language-filter {{ padding: 8px; border: 1px solid #ddd; border-radius: 4px; }}
                .page-filter {{ padding: 8px; border: 1px solid #ddd; border-radius: 4px; }}
                .screenshot {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; }}
                .tabs {{ display: flex; margin-bottom: 20px; }}
                .tab {{ padding: 10px 15px; cursor: pointer; border: 1px solid #ddd; border-radius: 4px 4px 0 0; border-bottom: none; }}
                .tab.active {{ background-color: #f8f9fa; font-weight: bold; }}
                .tab-content {{ display: none; }}
                .tab-content.active {{ display: block; }}
                .mismatch-details {{ display: flex; margin-top: 10px; }}
                .text-comparison {{ flex: 1; }}
                .visual-comparison {{ flex: 1; padding-left: 20px; }}
                .collapsible {{ background-color: #f8f9fa; cursor: pointer; padding: 10px; width: 100%; border: none; text-align: left; outline: none; }}
                .active, .collapsible:hover {{ background-color: #e9ecef; }}
                .collapsible-content {{ padding: 0 18px; display: none; overflow: hidden; }}
                .chart-container {{ width: 100%; height: 300px; margin-bottom: 20px; }}
            </style>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <div class="container">
                <h1>Translation Test Report</h1>
                <div class="summary">
                    <h2>Summary</h2>
                    <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Application:</strong> {self.config.get("base_url", "Unknown")}</p>
                    <p><strong>Excel File:</strong> {os.path.basename(self.config.get("excel_path", "Unknown"))}</p>
                    
                    <div class="stats">
                        <div class="stat-card">
                            <h3>Total Elements</h3>
                            <div class="stat-value">{self.results["total_elements"]}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Match Rate</h3>
                            <div class="stat-value {self._get_status_class(match_percentage)}">{match_percentage:.2f}%</div>
                        </div>
                        <div class="stat-card">
                            <h3>Total Mismatches</h3>
                            <div class="stat-value {self._get_status_class(100 - match_percentage)}">{total_mismatches}</div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <canvas id="languageChart"></canvas>
                    </div>
                </div>
                
                <div class="tabs">
                    <div class="tab active" onclick="openTab(event, 'mismatches')">Mismatches</div>
                    <div class="tab" onclick="openTab(event, 'pages')">Pages</div>
                    <div class="tab" onclick="openTab(event, 'config')">Configuration</div>
                </div>
                
                <div id="mismatches" class="tab-content active">
                    <div class="filter-controls">
                        <input type="text" class="search" id="mismatchSearch" placeholder="Search mismatches...">
                        <select class="language-filter" id="languageFilter">
                            <option value="">All Languages</option>
                            <option value="English">English</option>
                            <option value="Khmer">Khmer</option>
                            <option value="Chinese">Chinese</option>
                        </select>
                        <select class="page-filter" id="pageFilter">
                            <option value="">All Pages</option>
                            {self._generate_page_options()}
                        </select>
                    </div>
                    
                    <table id="mismatchTable">
                        <thead>
                            <tr>
                                <th>Page</th>
                                <th>Element</th>
                                <th>Language</th>
                                <th>Details</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._generate_mismatch_rows()}
                        </tbody>
                    </table>
                </div>
                
                <div id="pages" class="tab-content">
                    {self._generate_pages_content()}
                </div>
                
                <div id="config" class="tab-content">
                    <h2>Test Configuration</h2>
                    <table>
                        <tr>
                            <th>Parameter</th>
                            <th>Value</th>
                        </tr>
                        {self._generate_config_rows()}
                    </table>
                </div>
                
                <script>
                    // Chart generation
                    const ctx = document.getElementById('languageChart').getContext('2d');
                    const chartConfig = {json.dumps(self._get_chart_config(), indent=4)};
                    new Chart(ctx, chartConfig);
                    
                    // Tab functionality
                    function openTab(evt, tabName) {{
                        const tabContents = document.getElementsByClassName("tab-content");
                        for (let i = 0; i < tabContents.length; i++) {{
                            tabContents[i].className = tabContents[i].className.replace(" active", "");
                        }}
                        
                        const tabs = document.getElementsByClassName("tab");
                        for (let i = 0; i < tabs.length; i++) {{
                            tabs[i].className = tabs[i].className.replace(" active", "");
                        }}
                        
                        document.getElementById(tabName).className += " active";
                        evt.currentTarget.className += " active";
                    }}
                    
                    // Filtering functionality
                    document.getElementById('mismatchSearch').addEventListener('keyup', filterTable);
                    document.getElementById('languageFilter').addEventListener('change', filterTable);
                    document.getElementById('pageFilter').addEventListener('change', filterTable);
                    
                    function filterTable() {{
                        const search = document.getElementById('mismatchSearch').value.toLowerCase();
                        const languageFilter = document.getElementById('languageFilter').value;
                        const pageFilter = document.getElementById('pageFilter').value;
                        
                        const rows = document.getElementById('mismatchTable').getElementsByTagName('tbody')[0].getElementsByTagName('tr');
                        
                        for (let i = 0; i < rows.length; i++) {{
                            const page = rows[i].getElementsByTagName('td')[0].textContent;
                            const language = rows[i].getElementsByTagName('td')[2].textContent;
                            const text = rows[i].textContent.toLowerCase();
                            
                            let displayRow = true;
                            
                            if (search && !text.includes(search)) {{
                                displayRow = false;
                            }}
                            
                            if (languageFilter && language !== languageFilter) {{
                                displayRow = false;
                            }}
                            
                            if (pageFilter && page !== pageFilter) {{
                                displayRow = false;
                            }}
                            
                            rows[i].style.display = displayRow ? '' : 'none';
                        }}
                    }}
                    
                    // Collapsible sections
                    const coll = document.getElementsByClassName("collapsible");
                    for (let i = 0; i < coll.length; i++) {{
                        coll[i].addEventListener("click", function() {{
                            this.classList.toggle("active");
                            const content = this.nextElementSibling;
                            content.style.display = content.style.display === "block" ? "none" : "block";
                        }});
                    }}
                </script>
            </div>
        </body>
        </html>
        """
        
        # Write the HTML report
        with open(self.report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Report generated: {self.report_file}")
        return self.report_file
        
    def _get_status_class(self, percentage):
        """Get CSS class based on percentage"""
        if percentage >= 90:
            return "success"
        elif percentage >= 70:
            return "warning"
        else:
            return "error"
            
    def _generate_mismatch_rows(self):
        """Generate HTML table rows for mismatches"""
        rows = ""
        for idx, mismatch in enumerate(self.results.get("mismatches", [])):
            page = mismatch.get("page", "Unknown")
            element = mismatch.get("element", "Unknown")
            language = mismatch.get("language", "Unknown")
            actual = mismatch.get("actual", "")
            expected = mismatch.get("expected", "")
            
            screenshot_path = ""
            screenshot_name = f"mismatch_{language.lower()}_{page.replace(' > ', '_')}"
            screenshots_dir = self.config.get("screenshots_dir", "screenshots")
            
            # Find matching screenshots
            if os.path.exists(screenshots_dir):
                for file in os.listdir(screenshots_dir):
                    if file.startswith(screenshot_name) and file.endswith(".png"):
                        screenshot_path = os.path.join("..", screenshots_dir, file)
                        break
            
            rows += f"""
            <tr>
                <td>{page}</td>
                <td>{element}</td>
                <td>{language}</td>
                <td>
                    <button class="collapsible">View Details</button>
                    <div class="collapsible-content">
                        <div class="mismatch-details">
                            <div class="text-comparison">
                                <p><strong>Actual:</strong> <span style="background-color: #ffcccc;">{actual}</span></p>
                                <p><strong>Expected:</strong> <span style="background-color: #ccffcc;">{expected}</span></p>
                                <p><strong>Difference:</strong></p>
                                <div id="diff-{idx}" class="diff-display"></div>
                            </div>
                            {"<div class='visual-comparison'><img src='" + screenshot_path + "' class='screenshot' alt='Screenshot of mismatch'></div>" if screenshot_path else ""}
                        </div>
                    </div>
                </td>
            </tr>
            """
        return rows
    
    def _generate_page_options(self):
        """Generate options for page filter dropdown"""
        pages = set()
        for mismatch in self.results.get("mismatches", []):
            page = mismatch.get("page", "")
            if page:
                pages.add(page)
        
        options = ""
        for page in sorted(pages):
            options += f'<option value="{page}">{page}</option>'
        return options
        
    def _generate_pages_content(self):
        """Generate content for the Pages tab"""
        # Group mismatches by page
        pages_data = {}
        for mismatch in self.results.get("mismatches", []):
            page = mismatch.get("page", "Unknown")
            if page not in pages_data:
                pages_data[page] = {
                    "en_mismatched": 0,
                    "kh_mismatched": 0,
                    "cn_mismatched": 0,
                    "mismatches": []
                }
            
            lang_code = mismatch.get("language", "").lower()[:2]
            if lang_code in ["en", "kh", "cn"]:
                pages_data[page][f"{lang_code}_mismatched"] += 1
            
            pages_data[page]["mismatches"].append(mismatch)
        
        # Generate HTML for each page
        html = ""
        for page_name, page_data in sorted(pages_data.items()):
            total_mismatches = page_data["en_mismatched"] + page_data["kh_mismatched"] + page_data["cn_mismatched"]
            
            html += f"""
            <div class="page-section">
                <h3>{page_name}</h3>
                <div class="page-stats">
                    <p><strong>Total Mismatches:</strong> {total_mismatches}</p>
                    <p><strong>English Mismatches:</strong> {page_data["en_mismatched"]}</p>
                    <p><strong>Khmer Mismatches:</strong> {page_data["kh_mismatched"]}</p>
                    <p><strong>Chinese Mismatches:</strong> {page_data["cn_mismatched"]}</p>
                </div>
                
                <button class="collapsible">View Mismatches</button>
                <div class="collapsible-content">
                    <table class="page-mismatches">
                        <thead>
                            <tr>
                                <th>Element</th>
                                <th>Language</th>
                                <th>Actual</th>
                                <th>Expected</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for mismatch in page_data["mismatches"]:
                html += f"""
                <tr>
                    <td>{mismatch.get("element", "")}</td>
                    <td>{mismatch.get("language", "")}</td>
                    <td>{mismatch.get("actual", "")}</td>
                    <td>{mismatch.get("expected", "")}</td>
                </tr>
                """
            
            html += """
                        </tbody>
                    </table>
                </div>
            </div>
            """
        
        return html
    
    def _generate_config_rows(self):
        """Generate rows for configuration table"""
        rows = ""
        # Don't display sensitive information
        safe_config = self.config.copy()
        if "password" in safe_config:
            safe_config["password"] = "********"
        
        for key, value in safe_config.items():
            # Format lists and objects for better display
            if isinstance(value, list):
                if key == "navigation_paths":
                    display_value = "<br>".join([" > ".join(path) for path in value])
                else:
                    display_value = ", ".join(str(item) for item in value)
            elif isinstance(value, dict):
                display_value = "<br>".join([f"{k}: {v}" for k, v in value.items()])
            else:
                display_value = str(value)
            
            rows += f"""
            <tr>
                <td>{key}</td>
                <td>{display_value}</td>
            </tr>
            """
        return rows