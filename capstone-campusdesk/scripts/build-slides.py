"""Create the rubric-accepted PDF deck and render every page for visual review."""
from pathlib import Path
from xml.sax.saxutils import escape

import fitz
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "demo" / "slides.pdf"
PREVIEWS = ROOT / "evidence" / "local" / "slides"
PREVIEWS.mkdir(parents=True, exist_ok=True)
c = canvas.Canvas(str(OUT), pagesize=(960, 540))
c.setTitle("CampusDesk - DevOps Capstone - T. Abdul Kalam Azad")
c.setAuthor("T. Abdul Kalam Azad | 24BCS10053")
body = ParagraphStyle("body", fontName="Helvetica", fontSize=19, leading=29, textColor=HexColor("#41534b"))
small = ParagraphStyle("small", parent=body, fontSize=16, leading=24)
page_number = 0


def text(value, x, y, width=820, style=body):
    paragraph = Paragraph(value, style)
    _, height = paragraph.wrap(width, 500)
    assert y - height > 45, f"Text overflows slide {page_number}: {value}"
    paragraph.drawOn(c, x, y - height)
    return y - height


def start(title, section):
    global page_number
    page_number += 1
    c.setFillColor(HexColor("#ffffff"))
    c.rect(0, 0, 960, 540, fill=1, stroke=0)
    c.setFillColor(HexColor("#246b56"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(52, 494, section.upper())
    c.setFillColor(HexColor("#172c23"))
    c.setFont("Helvetica-Bold", 35)
    assert c.stringWidth(title, "Helvetica-Bold", 35) < 856, title
    c.drawString(52, 435, title)
    c.setFillColor(HexColor("#8a9690"))
    c.setFont("Helvetica", 10)
    c.drawString(52, 25, "T. Abdul Kalam Azad  |  24BCS10053  |  CampusDesk")
    c.drawRightString(908, 25, f"{page_number:02d}")


def bullets(items, y=365, width=815):
    for item in items:
        y = text(item, 60, y, width) - 21


start("CampusDesk", "DevOps Capstone")
c.setFont("Helvetica-Bold", 56)
c.setFillColor(HexColor("#172c23"))
c.drawString(52, 322, "Campus IT, organized.")
text("A helpdesk for campus requests, delivered through a tested container and Kubernetes workflow.", 55, 264, 730)
text("T. Abdul Kalam Azad<br/>24BCS10053", 55, 142, 700, small)
c.showPage()

start("Every request has a clear next step", "Application")
bullets(["Students report network, hardware, software and account issues.",
         "The support team sets priority, assigns an owner and resolves tickets.",
         "Search and status filters make the queue easier to manage.",
         "Synthetic demo tickets exercise the same APIs as newly created requests."])
c.showPage()

start("One application, three core layers", "Technology")
bullets(["React + Vite + Nginx deliver the responsive service desk.",
         "FastAPI validates requests; SQLAlchemy manages database operations.",
         "PostgreSQL persists tickets; Alembic versions the schema.",
         "Python tests and Ruff catch regressions before image publication."])
c.showPage()

start("Traffic and changes follow defined paths", "Architecture")
diagram = ROOT / "evidence" / "architecture.png"
if diagram.exists():
    c.drawImage(str(diagram), 52, 78, width=856, height=320, preserveAspectRatio=True, anchor="c")
c.showPage()

start("The service desk runs in the browser", "Working application")
screenshot = ROOT / "evidence" / "application-desktop.png"
if screenshot.exists():
    c.drawImage(str(screenshot), 52, 67, width=856, height=337, preserveAspectRatio=True, anchor="c")
c.showPage()

start("Quality gates precede publication", "CI/CD and security")
bullets(["Ruff, database migrations, pytest and the frontend build run first.",
         "Both images are scanned for HIGH and CRITICAL vulnerabilities.",
         "The Helm release is smoke-tested in an ephemeral Kind cluster.",
         "Successful main-branch runs publish images tagged with the commit SHA."])
c.showPage()

start("Kubernetes manages application replicas", "Deployment")
bullets(["Helm defines Deployments, Services, Secrets and PostgreSQL storage.",
         "Traefik routes the UI and API through one Ingress hostname.",
         "Readiness checks database access; liveness checks the process.",
         "Metrics Server supports an HPA with a range of two to four API replicas."])
c.showPage()

start("Git records the desired deployment", "GitOps")
bullets(["Argo CD reads the CampusDesk Helm chart from the GitHub repository.",
         "Sync compares the committed configuration with the running cluster.",
         "Migration ordering prepares the database before application rollout.",
         "CI promotes scanned image tags; automatic sync deploys that Git revision."])
c.showPage()

start("Metrics explain what the service is doing", "Observability")
bullets(["Prometheus discovers and scrapes each backend replica.",
         "Grafana shows request rate, p95 latency, status codes and availability.",
         "A bounded load generator creates real API traffic for the dashboard.",
         "Backend availability and error-ratio alert rules detect service problems."])
c.showPage()

start("AWS infrastructure is prepared in code", "Terraform - deployment deferred")
bullets(["Two public subnets and two private subnets span availability zones.",
         "A NAT gateway connects private worker nodes to external registries.",
         "EKS, a managed node group and EBS CSI provide the deployment foundation.",
         "Cloud plan, apply, console evidence and destroy remain pending AWS access."])
c.showPage()

start("Failures become evidence for diagnosis", "Troubleshooting")
bullets(["A nonexistent image tag demonstrates ImagePullBackOff and pod events.",
         "A wrong Service selector demonstrates missing endpoints.",
         "A failed database connection makes readiness return HTTP 503.",
         "Image scans guide remediation; successful deployment alone is not security proof."])
c.showPage()

start("Verification is part of the deliverable", "Learnings and remaining work")
bullets(["A working app needs tests, repeatable deployment and observable behavior.",
         "Screenshots and reports should show actual runs and identify their environment.",
         "Complete the deferred AWS deployment and record its real evidence.",
         "Use the repository submission checklist before presenting the final walkthrough."])
text("Brief, rubric and submission guide: github.com/Nency-Ravaliya/devsecops-python", 60, 95, 815, small)
c.showPage()
c.save()

document = fitz.open(OUT)
for index, page in enumerate(document):
    page.get_pixmap(matrix=fitz.Matrix(1.3, 1.3)).save(PREVIEWS / f"slide-{index + 1:02d}.png")
    assert len(page.get_text().strip()) > 20
print(f"Created and rendered {len(document)} slides: {OUT}")
