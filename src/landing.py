from dotenv import dotenv_values
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from lxml import etree
import markdown
import os
import re
import shutil

env_vars = dotenv_values(".env")

def main():
    jinja2_env = Environment(loader=FileSystemLoader("src/templates"), autoescape=False)
    sitemap_src = etree.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    dist_path = "dist/landing"
    sitemap_exclude = ["404.md"]
    navigation_exclude = ["404.md", "index.md"]
    src_md_path = "src/markdown"
    src_static_path = "src/static_root"

    shutil.rmtree(dist_path, True)
    shutil.copytree(src_static_path, dist_path)

    NAVIGATION = []
    for file in sorted(os.listdir(src_md_path)):
        # Prepare navigation links data
        if file not in navigation_exclude:
            slug = file.replace("_", "/").replace(".md", "")
            name = file.replace("_", " ").replace("-", " ").replace(".md", "").title()
            NAVIGATION.append({"name": name, "slug": slug})

        # Prepare sitemap data
        if file not in sitemap_exclude:
            url_element = etree.SubElement(sitemap_src, "url")
            slug = (
                file.replace("_", "/").replace(".md", "")
                if file != "index.md"
                else ""
            )
            etree.SubElement(url_element, "loc").text = f"{env_vars['SITE_URL']}/{slug}"

    # Write sitemap to disk
    with open(f"{dist_path}/sitemap.xml", "w") as file:
        file.write(etree.tostring(sitemap_src).decode("utf8"))

    for file in os.listdir(src_md_path):
        # Prepare static pages data
        file_path = f"{src_md_path}/{file}"
        dist_file = file.replace(".md", ".html")
        dist_file_path = f"{dist_path}/{dist_file}"
        try:
            templates = jinja2_env.get_template(dist_file)
        except TemplateNotFound:
            templates = jinja2_env.get_template("default.html")

        # Prepare template data
        with open(file_path, "r") as f:
            file_content = f.read()
            jinja2_html = templates.render(
                content=markdown.markdown(
                    file_content,
                    extensions=["tables", "fenced_code", "codehilite", "toc"],
                ),
                **{key: value for key, value in re.findall(r"<!--\s*(.*?):\s*(.*?)\s*-->", file_content)},
                **env_vars,
                NAVIGATION=NAVIGATION,
                slug=slug,
                created=os.path.getctime(file_path),
                modified=os.path.getmtime(file_path),
            )

        # Write static page to disk
        with open(dist_file_path, "w") as f:
            f.write(jinja2_html)

main()
