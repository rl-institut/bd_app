import markdown
from django.conf import settings
from django.views.generic import TemplateView


class LandingPage(TemplateView):
    template_name = "pages/home.html"


class ContactPage(TemplateView):
    template_name = "pages/contact.html"


class ImprintPage(TemplateView):
    template_name = "pages/imprint.html"


class PrivacyPage(TemplateView):
    template_name = "pages/privacy.html"


class DocumentationView(TemplateView):
    template_name = "docs.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = kwargs.get("page", "index")
        page = page if page.endswith(".md") else f"{page}.md"
        if not (settings.DOCS_DIR / page).exists():
            error_msg = f"Documentation for '{page}' not found."
            raise FileNotFoundError(error_msg)
        with (settings.DOCS_DIR / page).open("r", encoding="utf-8") as f:
            markdown_text = f.read()
        context["markdown"] = markdown.markdown(markdown_text, output_format="html")
        return context
