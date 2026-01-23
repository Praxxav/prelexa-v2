from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks, HTTPException
from typing import Optional
import os
import logging
import json
from datetime import datetime
from app.utils.dependencies import get_org_id, get_user_id, get_user_id
from app.utils.uploads import UPLOAD_DIR
from app.services.stt_service import transcribe_audio_file
from app.agent.document_agent import analyze_document_text
from db.database import db
from app.services.document_variable_service import DocumentVariableService

router = APIRouter(prefix="/recordings", tags=["recordings"])
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_recording(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form("New Recording"),
    org_id: str = Depends(get_org_id),
    user_id: str = Depends(get_user_id)
):
    try:
        # 1. Save File
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = f"rec_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(file_path, "wb") as f:
            f.write(await file.read())
            
        # 2. Transcribe (Await for now, or background if long?)
        # For better UX, we await so we can create the document with text immediately
        # or we create document first then background transcribe.
        # User wants "Listen the Audio and create the document".
        
        transcript = await transcribe_audio_file(file_path)
        
        if not transcript:
            transcript = "(No speech detected)"

        # 3. Create Document
        doc = await db.document.create(
            data={
                "status": "processing", # Will process insights in background
                "filePath": file_path,
                "orgId": org_id,
                "userId": user_id,
                "fullText": transcript,
                "documentType": "Meeting Recording",
                "metadata": json.dumps({"title": title}),
            }
        )

        # 4. Create Meeting Record (so it shows in Dashboard)
        try:
            meeting_id = str(uuid.uuid4())
            await db.meeting.create(
                data={
                    "orgId": org_id,
                    "meetingId": meeting_id,
                    "title": title,
                    "startedAt": datetime.now(), 
                    "documentId": doc.id,
                    "creatorId": user_id,
                    "participants": "[]"
                }
            )
        except Exception as e:
            logger.error(f"Failed to create meeting record: {e}")
            # Don't fail the upload if meeting creation fails, but log it.


        # 4. Background Analysis (Agent)
        background_tasks.add_task(process_recording_insights, doc.id, transcript)

        return {"message": "Recording processed", "document_id": doc.id}

    except Exception as e:
        logger.error(f"Recording upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def process_recording_insights(doc_id: str, text: str):
    try:
        if not text or text == "(No speech detected)":
             await db.document.update(
                where={"id": doc_id},
                data={"status": "completed"}
            )
             return

        analysis = await analyze_document_text(text)
        
        if "error" in analysis:
            await db.document.update(
                where={"id": doc_id},
                data={"status": "failed"} 
            )
            return

        await db.document.update(
            where={"id": doc_id},
            data={
                "status": "completed",
                "documentType": analysis.get("document_type", "Meeting Recording"),
                "insights": json.dumps(analysis),
                 # Update title if agent thinks of a better one? Maybe keep user title.
            },
        )

        fields = analysis.get("fields", [])
        if fields:
            await DocumentVariableService.bulk_create_variables(
                doc_id,
                [
                    {
                        "name": f["name"],
                        "value": str(f.get("value", "")),
                        "confidence": f.get("confidence", 1.0),
                        "editable": f.get("editable", True),
                    }
                    for f in fields
                ],
            )

    except Exception as e:
        logger.error(f"[{doc_id}] Insight processing failed: {e}", exc_info=True)
        await db.document.update(
            where={"id": doc_id},
            data={"status": "failed"}
        )
