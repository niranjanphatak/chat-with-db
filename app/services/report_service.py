import json
import csv
import os
from datetime import datetime
from typing import Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from app.services.database import db_service
from app.models.schemas import ReportResponse
from bson import json_util
import logging

logger = logging.getLogger(__name__)


class ReportService:
    def __init__(self):
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_report(self, report_name: str, pipeline: list,
                        output_format: str = "json") -> ReportResponse:
        """Generate a report based on aggregation pipeline results"""

        # Execute the aggregation
        results = db_service.execute_aggregation(pipeline)

        # Serialize results
        serialized_results = json.loads(json_util.dumps(results))

        # Generate summary statistics
        summary = self._generate_summary(serialized_results)

        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() else "_" for c in report_name[:30])

        file_path = None

        if output_format == "csv":
            file_path = self._generate_csv(serialized_results, safe_name, timestamp)
        elif output_format == "pdf":
            file_path = self._generate_pdf(serialized_results, report_name, safe_name, timestamp)
        elif output_format == "json":
            file_path = self._generate_json(serialized_results, safe_name, timestamp)

        return ReportResponse(
            report_name=report_name,
            generated_at=datetime.now(),
            query_used={"pipeline": pipeline},
            data=serialized_results,
            summary=summary,
            file_path=file_path
        )

    def _generate_summary(self, results: list) -> dict:
        """Generate summary statistics from results"""
        summary = {
            "total_records": len(results),
            "generated_at": datetime.now().isoformat()
        }

        if not results:
            return summary

        # Try to calculate numeric summaries
        numeric_fields = {}
        for record in results:
            for key, value in record.items():
                if isinstance(value, (int, float)) and key != "_id":
                    if key not in numeric_fields:
                        numeric_fields[key] = []
                    numeric_fields[key].append(value)

        for field, values in numeric_fields.items():
            summary[f"{field}_total"] = sum(values)
            summary[f"{field}_avg"] = round(sum(values) / len(values), 2) if values else 0
            summary[f"{field}_max"] = max(values) if values else 0
            summary[f"{field}_min"] = min(values) if values else 0

        return summary

    def _generate_json(self, results: list, safe_name: str, timestamp: str) -> str:
        """Generate JSON report file"""
        file_path = os.path.join(self.reports_dir, f"{safe_name}_{timestamp}.json")

        with open(file_path, 'w') as f:
            json.dump({
                "report_name": safe_name,
                "generated_at": timestamp,
                "data": results,
                "summary": self._generate_summary(results)
            }, f, indent=2, default=str)

        logger.info(f"Generated JSON report: {file_path}")
        return file_path

    def _generate_csv(self, results: list, safe_name: str, timestamp: str) -> str:
        """Generate CSV report file"""
        file_path = os.path.join(self.reports_dir, f"{safe_name}_{timestamp}.csv")

        if not results:
            with open(file_path, 'w') as f:
                f.write("No data available")
            return file_path

        # Flatten nested dictionaries for CSV
        flattened_results = []
        for record in results:
            flat_record = self._flatten_dict(record)
            flattened_results.append(flat_record)

        # Get all unique keys
        all_keys = set()
        for record in flattened_results:
            all_keys.update(record.keys())

        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()
            writer.writerows(flattened_results)

        logger.info(f"Generated CSV report: {file_path}")
        return file_path

    def _generate_pdf(self, results: list, report_name: str,
                      safe_name: str, timestamp: str) -> str:
        """Generate PDF report file"""
        file_path = os.path.join(self.reports_dir, f"{safe_name}_{timestamp}.pdf")

        doc = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30
        )

        # Title
        elements.append(Paragraph(report_name, title_style))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                  styles['Normal']))
        elements.append(Spacer(1, 20))

        # Summary section
        summary = self._generate_summary(results)
        elements.append(Paragraph("Summary", styles['Heading2']))
        for key, value in summary.items():
            elements.append(Paragraph(f"{key}: {value}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # Data table
        if results:
            elements.append(Paragraph("Data", styles['Heading2']))

            # Flatten results for table
            flattened = [self._flatten_dict(r) for r in results]

            if flattened:
                # Get headers
                headers = list(flattened[0].keys())

                # Truncate headers and values for display
                table_data = [[self._truncate(h, 15) for h in headers]]

                for record in flattened[:50]:  # Limit to 50 rows
                    row = [self._truncate(str(record.get(h, '')), 20) for h in headers]
                    table_data.append(row)

                # Create table
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)

                if len(results) > 50:
                    elements.append(Spacer(1, 10))
                    elements.append(Paragraph(
                        f"Showing 50 of {len(results)} records",
                        styles['Normal']
                    ))

        doc.build(elements)
        logger.info(f"Generated PDF report: {file_path}")
        return file_path

    def _flatten_dict(self, d: dict, parent_key: str = '', sep: str = '_') -> dict:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _truncate(self, text: str, length: int) -> str:
        """Truncate text to specified length"""
        text = str(text)
        return text[:length] + '...' if len(text) > length else text


# Singleton instance
report_service = ReportService()
