from fastapi import FastAPI, UploadFile, File, Form, Response
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
import pymupdf
from PIL import Image
from io import BytesIO
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# CORS
# Укажите разрешенные источники
origins = [
    "http://localhost:5173",
    "https://petrovkirill.ru",  # Продакшен-домен
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Разрешенные источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешенные методы (GET, POST и т.д.)
    allow_headers=["*"],  # Разрешенные заголовки
)


@app.post("/api/ListPDF/merge/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    pdf_paths = []

    for file in files:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        pdf_paths.append(file_path)

    return JSONResponse(content={"files": [file.filename for file in files]})


@app.get("/api/ListPDF/merge/thumbnail/{filename}")
async def thumbnail(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return JSONResponse(content={"error": "File not found"}, status_code=404)

    pdf = pymupdf.open(file_path)
    first_page = pdf[0]
    pix = first_page.get_pixmap()

    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img.thumbnail((80, 113))

    img_io = BytesIO()
    img.save(img_io, "PNG")
    img_io.seek(0)

    return StreamingResponse(img_io, media_type="image/png")


def combine_pdfs(pdf_paths):
    combined_pdf_path = os.path.join(UPLOAD_FOLDER, "combined_output.pdf")

    # Проверка, есть ли файлы
    if not pdf_paths:
        raise ValueError("Нет PDF-файлов для объединения.")

    combined_pdf = pymupdf.open()

    for pdf_path in pdf_paths:
        full_path = os.path.join(UPLOAD_FOLDER, pdf_path)  # Добавляем путь
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Файл {pdf_path} не найден.")

        pdf = pymupdf.open(full_path)
        combined_pdf.insert_pdf(pdf)

    combined_pdf.save(combined_pdf_path)
    combined_pdf.close()
    return combined_pdf_path



class MergeRequest(BaseModel):#класс для приёма данных с фронта
    files: List[str]

@app.post("/api/ListPDF/merge/combine")
async def merge_pdfs(request: MergeRequest):
    print("Received file names:", request.files)

    try:
        output_pdf = combine_pdfs(request.files)

        # Проверяем, что файл действительно существует
        if os.path.exists(output_pdf) and os.path.getsize(output_pdf) > 0:
            return Response(content=open(output_pdf, "rb").read(), media_type="application/pdf")
        else:
            return {"error": "Ошибка при создании PDF"}

    except Exception as e:
        return {"error": str(e)}


@app.post("/api/ListPDF/split/extract")
async def split_pdf(file: UploadFile = File(...), start_page: int = Form(...), end_page: int = Form(...)):
    try:
        filename = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(filename, "wb") as f:
            f.write(await file.read())

        pdf = pymupdf.open(filename)
        total_pages = pdf.page_count

        if start_page <= 0 or end_page <= 0 or start_page > end_page or end_page > total_pages:
            return JSONResponse(content={"error": "Invalid page range"}, status_code=400)

        split_pdf = pymupdf.open()
        for page_num in range(start_page - 1, end_page):
            split_pdf.insert_pdf(pdf, from_page=page_num, to_page=page_num)

        output_stream = BytesIO()
        split_pdf.save(output_stream)
        split_pdf.close()
        output_stream.seek(0)

        return StreamingResponse(output_stream, media_type="application/pdf",
                                 headers={"Content-Disposition": f"attachment; filename=split_{file.filename}"})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/api/ListPDF/pdf_to_img")
async def pdf_to_image(file: UploadFile = File(...), page_number: int = Form(...)):
    try:
        filename = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(filename, "wb") as f:
            f.write(await file.read())

        pdf_document = pymupdf.open(filename)
        if page_number < 1 or page_number > len(pdf_document):
            return JSONResponse(content={"error": "Page number out of range"}, status_code=400)

        page = pdf_document[page_number - 1]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        pdf_document.close()
        os.remove(filename)

        return StreamingResponse(img_buffer, media_type="image/png",
                                 headers={"Content-Disposition": "attachment; filename=page.png"})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/api/ListPDF/img_to_pdf")
async def img_to_pdf(images: list[UploadFile] = File(...)):
    try:
        valid_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif")
        images_list = []

        for img_file in images:
            if not img_file.filename.lower().endswith(valid_extensions):
                return JSONResponse(content={"error": f"Unsupported file type: {img_file.filename}"}, status_code=400)

            img = Image.open(BytesIO(await img_file.read()))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            images_list.append(img)

        pdf_stream = BytesIO()
        if len(images_list) == 1:
            images_list[0].save(pdf_stream, format="PDF")
        else:
            images_list[0].save(pdf_stream, format="PDF", save_all=True, append_images=images_list[1:])

        pdf_stream.seek(0)
        return StreamingResponse(pdf_stream, media_type="application/pdf",
                                 headers={"Content-Disposition": "attachment; filename=converted_images.pdf"})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
