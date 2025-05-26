import traceback
from jinja2 import Template, TemplateError, FileSystemLoader, Environment

class Test:


    def transform(self) -> str:
        #
        # leave these imports here. they are super slow.
        # so we don't want the latency in testing or ever
        # unless we're actually rendering a template.
        #
        #import inflect  # pylint: disable=C0415
        #self._engine = inflect.engine()
        content = None
        try:
            #t = Template(template)
            e = Environment(loader=FileSystemLoader("flightpath/assets/help/templates/"))
            t = e.get_template("function_description.html")

            tokens = {}
            content = t.render(data=tokens)
        except TemplateError:
            print(traceback.format_exc())
        return content

if __name__ == "__main__":

    test = Test()
    s = test.transform()
    print(s)

