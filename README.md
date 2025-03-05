# petrovkirill.ru-backend
Repository for the backend of my website petrovkirill.ru. Uses FastAPI web framework to create API in Python. Provides high application performance due to the use of asynchronous programming methods. PyMuPDF: A library for working with PDF documents. Also used by pillow, pydantic, io, cors.

## Backend Structure

### ListPDF Project (/ListPDF)

- **Merge**
  - **Upload Files** (`/api/ListPDF/merge/upload`)
    - Upload PDF files for later merging.
  - **Thumbnail** (`/api/ListPDF/merge/thumbnail/{filename}`)
    - Generates a thumbnail of the first page of the PDF.
  - **Combine PDFs** (`/api/ListPDF/merge/combine`)
    - Combine downloaded PDF files into a single document.

- **Split**
  - **Extract Pages** (`/api/ListPDF/split/extract`)
    - Extract a range of pages from a PDF document.

- **PDF to Image**
  - **Convert Page to Image** (`/api/ListPDF/pdf_to_img`)
    - Converts the specified PDF page into an image.

- **Image to PDF**
  - **Convert Images to PDF** (`/api/ListPDF/img_to_pdf`)
    - Convert downloaded images into a PDF document.
