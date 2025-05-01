import traceback

class HtmlGenerator:

    @classmethod
    def load_and_transform(self, path:str, tokens:dict[str,str]) -> None:
        page = None
        with open(path, "r", encoding="utf-8") as file:
            page = file.read()
        page = self.transform(template=page, tokens=tokens)
        return page

    @classmethod
    def transform(self, template: str, tokens: dict[str, str] = None) -> str:
        #
        # leave these imports here. they are super slow.
        # so we don't want the latency in testing or ever
        # unless we're actually rendering a template.
        #
        from jinja2 import Template, TemplateError  # pylint: disable=C0415
        #import inflect  # pylint: disable=C0415

        #self._engine = inflect.engine()
        try:
            t = Template(template)
            content = t.render(data=tokens)
        except TemplateError:
            print(traceback.format_exc())
        return content
