import traceback
import os

class HtmlGenerator:

    @classmethod
    def load_and_transform(self, path:str, tokens:dict[str,str]) -> None:
        page = None
        with open(path, "r", encoding="utf-8") as file:
            page = file.read()
        page = self.transform(path=path, template=page, tokens=tokens)
        return page

    @classmethod
    def transform(self, *, template: str, tokens: dict[str, str] = None, path:str = None) -> str:
        #
        # leave these imports here. they are super slow.
        # so we don't want the latency in testing or ever
        # unless we're actually rendering a template.
        #
        from jinja2 import Template, TemplateError, FileSystemLoader, Environment  # pylint: disable=C0415
        content = None
        try:
            i = path.find(f"{os.sep}help{os.sep}")
            dirname = path[0:i+6]
            basename = path[i+6:]
            print(f"htmlgen: transform: dirname: {dirname}")
            print(f"htmlgen: transform: basename: {basename}")

            #e = Environment(loader=FileSystemLoader(os.path.dirname(path)))
            e = Environment(loader=FileSystemLoader(dirname))
            t = e.get_template( basename )
            #t = e.get_template(os.path.basename(path))
            content = t.render(data=tokens)
        except TemplateError:
            print(traceback.format_exc())
        return content
