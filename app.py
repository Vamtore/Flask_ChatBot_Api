import os
#import cv2
import json
#import bottle
#import spacy
import random
import secrets
#import easyocr
#import wikipedia
#from wit import Wit
from bson import json_util
#from pylab import rcParams
from pymongo import MongoClient
# import matplotlib.pyplot as plt
# from IPython.display import Image
from fuzzywuzzy import fuzz,process
from bson.json_util import dumps, loads
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, url_for
from io import StringIO
# from pdfminer.converter import TextConverter
# from pdfminer.layout import LAParams
# from pdfminer.pdfdocument import PDFDocument
# from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
# from pdfminer.pdfpage import PDFPage
# from pdfminer.pdfparser import PDFParser

app = Flask(__name__)


try:
    client = MongoClient('localhost', 27017)
    db = client['faqdb']
    faqcol  = db['faqmongo']
    faqcol.insert({2:"sdfd"})

except:
    print("somthing went wrong in database connection!!")

UPLOAD_FOLDER = "C:\\Users\\Mahendra\\Desktop\\Dachrs\\bot-microservice\\picture"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def save_file(from_file):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(from_file.filename)
    file_fn = random_hex + f_ext
    file_path = os.path.join(app.root_path, 'picture', file_fn)
    from_file.save(file_path)
    return file_fn


@app.route("/get_data", methods=["GET"])
def get_seeds():
    all_seeds = list(faqcol.find({}))
    return json.dumps(all_seeds, default=json_util.default)

@app.route('/')
def index():
    return '''
         <form method="POST" action="/pdf_reader" enctype="multipart/form-data">
             <input type="text" name="username" required>
             <input type="file" name="user_upload">
             <input type="submit">
         </form>
    '''

@app.route('/image_read', methods = ['POST'])
def success():
    if request.method == "POST":
       #'user_upload' in request.files:

        user_upload = request.files['user_upload']
        file_upload = save_file(user_upload)
        faqcol.insert({'username': request.form.get('username'), 'photo_name': file_upload})


        rcParams['figure.figsize'] = 8, 16
        reader = easyocr.Reader(['en'])
        Image(f'picture/{file_upload}')
        output = reader.readtext(f'picture/{file_upload}')
        cord = output[-1][0]
        x_min, y_min = [int(min(idx)) for idx in zip(*cord)]
        x_max, y_max = [int(max(idx)) for idx in zip(*cord)]
        image = cv2.imread(f'picture/{file_upload}')
        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 0, 255), 2)
        plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        text = ''
        for result in output:
            text += result[1] + ''
        os.unlink(os.path.join(app.root_path,"picture", file_upload))
        return text


@app.route('/Spacy', methods = ['POST'])
def func_spcy_text():
    quest = request.json['user_quest']
    user_quest = quest
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(user_quest)
    for ent in doc.ents:
        return (f'{ent.text:{15}} {ent.start_char:{15}} {ent.end_char:{20}}  {ent.label_:{20}} {spacy.explain(ent.label_)} ')

    '''
    user_txt = ""
    client=Wit('NYQ2ZYOSKB3LVGXYDKLIDZAMZLKTCWPD')
    main_dict=client.message(user_txt)
    print(main_dict)
    ent_dict=main_dict['entities']
    keys=ent_dict.keys()
    li=[]
    st = ""
    for key in keys:
        pro_list=ent_dict[key]
        val=pro_list[0]['body']
        li.append(val)
    for i in li:
        st+=i
        st+=" "
    return st
    #values=filter_values(user_txt=txt,token=token)
    #print(values)
    '''



@app.route("/answer", methods=["POST"])
#@cross_origin(origin='*')
def add_data():

    #quest = request.get_json()['user_quest']
    quest = request.json['user_quest']
    user_quest = quest

    def get_matcher(query, choice, limit=3):
        result = process.extract(query, choice, limit=limit)
        quer=result
        return quer[0][0], quer[0][1],quer

    faqcol.insert({"title": "userfaq", "user_quest": [{"question": "quest"}]})
    #faqcol.update({"title": "userfaq"}, {"$push": {"user_quest": {"question": quest}}})
    if not quest:
        return jsonify({"Error": "Please Enter a Valid Question!!"})
    else:

        try:
            Get_Answer = faqcol.find_one({"FAQ": {"$elemMatch": {"question": quest}}},
                                         {"FAQ.answer.$": 1, "FAQ.faqtype": "Returns", "FAQ._id": 1})
            answer = ""
            for i in Get_Answer["FAQ"]:
                answer = i['answer']
            if Get_Answer:
                return jsonify({"Answer": answer})


        except:
            data= list(faqcol.find())

            question = []
            json_data=[]
            for t in data:
                if t.get('FAQ'):
                 for x in t.get('FAQ'):
                      json_data.append(x)

                      wwe = {"question":x.get('question')}
                      question.append(wwe)

            def prede_ans(data, user_quest, con_level):
                cont = json_data
                for ct in cont:
                    if ct['question'] == user_quest and con_level > 80:
                        return jsonify({"Answer": ct['answer']})

            quest_fuzz, confidence_level, question_info = get_matcher(user_quest, choice=question, limit=3)
            ans = prede_ans(data=data, user_quest=quest_fuzz, con_level=confidence_level)

            if ans != None:
                return jsonify({"Answer":ans, "Confidence Level":confidence_level})
            else:
                return jsonify({"Default":"sorry,I am unable to get you question ", "Confidence Level":confidence_level, "Question Information":question_info})

        else:
             return jsonify({"ERROR": "Something Went Wrong!!"})


@app.route("/pdf_reader", methods=["POST"])
def pdf2text():
    user_upload = request.files['user_upload']
    file_upload = save_file(user_upload)
    faqcol.insert({'username': request.form.get('username'), 'photo_name': file_upload})

    output_string = StringIO()
    in_file = open(f'picture/{file_upload}', 'rb')
    parser = PDFParser(in_file)
    doc = PDFDocument(parser)
    rsrcmgr = PDFResourceManager()
    device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.create_pages(doc):
        interpreter.process_page(page)

    text = output_string.getvalue()

    text = text.encode('utf-8')
    os.unlink(os.path.join(app.root_path, "picture", file_upload))
    return text

#file = open(f'{save_file_name}' + '.txt', 'wb')
#file.write(text)
#file.close()

#f = f'picture/{file_upload}'
#file = 'pree'
#pdf2text(f, file)



@app.route("/insert_data", methods=["POST"])
def insert_data():
        #Below code to Open Json file and deserialize object containing json document to python object
        with open('faq23.json') as input_json:
            json_data = json.load(input_json)
        # insert many if data contains list if not insert_one.
        if isinstance(json_data, list):
            print("List of documents availble in json")
            faqcol.insert_many(json_data)
        else :
            print("Single documents availble in json")
            faqcol.insert_one(json_data)


if __name__ == "__main__":
    app.run(port = 8001, debug=True)
