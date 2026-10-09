from io import BytesIO
from openpyxl import Workbook
from fastapi.responses import StreamingResponse


def export_report_to_excel(headers, rows, filename):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Report"

    worksheet.append(headers)

    for row in rows:
        worksheet.append(list(row))

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )