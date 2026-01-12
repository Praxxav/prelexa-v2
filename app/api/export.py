from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
import tempfile, json, os
from app.services.export_service import create_docx_from_markdown, fill_docx_template
from db.database import db as prisma

router = APIRouter(tags=["Export"])

@router.post("/")
async def export_document(
    variables: str = Form(...),
    export_type: str = Form(...),
    template_id: str = Form(...),
    file: UploadFile = File(None)
):
    """
    Exports a filled document using either an uploaded file or an existing template from Prisma DB.
    """
    print("\n=== EXPORT REQUEST ===")
    print(f"Template ID: {template_id}")
    print(f"Export Type: {export_type}")
    print(f"Has File Upload: {file is not None}")
    
    # ✅ Parse variables JSON
    try:
        variables_dict = json.loads(variables)
        print(f"Variables: {list(variables_dict.keys())}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON in variables: {e}")

    # ✅ Validate export type
    if export_type not in ["docx", "pdf"]:
        raise HTTPException(status_code=400, detail="export_type must be 'docx' or 'pdf'")

    # ✅ Get template content
    template = None
    
    if file is not None:
        # Use uploaded file
        contents = await file.read()
        temp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        temp_in.write(contents)
        temp_in.close()
        template_path = temp_in.name
        print(f"📁 Using uploaded file: {template_path}")
        
    elif template_id:
        # Fetch from Prisma database
        try:
            template = await prisma.template.find_unique(
                where={"id": template_id}
            )
        except Exception as e:
            print(f"❌ Database error: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
        if not template:
            print(f"❌ Template not found in database: {template_id}")
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
        
        print(f"📋 Found template: {template.title}")
        
        # Create a temporary DOCX from the markdown content
        try:
            # Access the bodyMd field (Prisma uses camelCase)
            template_path = create_docx_from_markdown(
                template.bodyMd,  # Prisma field name is camelCase
                template.title
            )
            print(f"📁 Created temp DOCX: {template_path}")
        except Exception as e:
            print(f"❌ Error creating DOCX from markdown: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Either file or template_id is required")

    # ✅ Fill template with variables
    try:
        output_path = fill_docx_template(template_path, variables_dict, export_type)
        print(f"✅ Document generated: {output_path}")
    except Exception as e:
        print(f"❌ Error filling template: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating document: {str(e)}")

    # ✅ Clean up temporary template if we created one
    if file is None and template_id:
        try:
            os.unlink(template_path)
            print(f"🗑️ Cleaned up temp template: {template_path}")
        except:
            pass

    # ✅ Determine media type and filename
    media_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document" 
        if export_type == "docx" 
        else "application/pdf"
    )
    
    # Use template title if available
    if template:
        filename = f"{template.title.replace(' ', '_').replace('/', '_')}.{export_type}"
    else:
        filename = f"document.{export_type}"
    
    print(f"📤 Sending file: {filename}")
    
    # ✅ Return the file
    return FileResponse(
        output_path,
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )