#Developed by neechalkaran@gmail.com
import flask
from flask import request, jsonify
import chatwiki
import markdown
import markdown.extensions.fenced_code
from flask_cors import CORS

app = flask.Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)

@app.route("/api")
def chat_api():
    quest= request.args.get("q")
    i_hierarchy={"Q24040821":"Q1445",#தமிழக முதல்வர் -தமிழ்நாடு
             "Q12983261":"Q1445"#தமிழக ஆளுநர்- தமிழ்நாடு
             }
    p_hierarchy={"P131":"P17"}

    errmsg="விக்கித்தரவில்   இல்லாமலோ vaaninlpயில் இல்லாமலோ இருக்கலாம்..."
    notamil="கேள்வி புரியவில்லை"
    token = chatwiki.word_tokenize(quest)
    entity = chatwiki.get_entities(token)
    root = chatwiki.get_roots(token)
    item = ""
    prop = ""
    if(len(token)<2):
       return jsonify(status=notamil), 200
    item = chatwiki.getQid_in_label_from_API([entity, root, token])
    if(item==""):
       return jsonify(status=errmsg), 200

    prop = chatwiki.getProp_in_label_from_API([entity, root, token])
    if(prop==""):
       return jsonify(status=errmsg), 200

    result = chatwiki.getlabel_in_from_sparql(item, prop)

    if(result=="" and item in i_hierarchy):
       result= chatwiki.getlabel_in_from_sparql(i_hierarchy[item],prop)
    if(result=="" and prop in p_hierarchy):
       result= chatwiki.getlabel_in_from_sparql(item, p_hierarchy[prop])


    try:
       return jsonify(answer=chatwiki.date_string(result)), 200
    except :
       return jsonify(answer=result),200

    return jsonify(status=errmsg), 200





@app.route("/")
def index():
    #return "Tamil chatBOT for Wikidata using VaaniNLP, a Tamil NLP library."
    readme_file = open('README.md', 'r')
    md_template_string = markdown.markdown(readme_file.read(), extensions=["fenced_code"])
    return md_template_string

if __name__ == "__main__":
    app.run()
