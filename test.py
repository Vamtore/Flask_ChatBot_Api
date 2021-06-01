from bson import json_util
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.json_util import dumps
from bson.json_util import loads
from bson import json_util
import random
import pytesseract as pt
import cv2
from PIL import Image
import json
import easyocr
import wikipedia


app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client['mongodb']
faqcol = db['mongocol']


@app.route("/get_data", methods=["GET"])
def get_seeds():
    all_seeds = list(faqcol.find({}))
    return json.dumps(all_seeds, default=json_util.default)


@app.route('/image_read', methods = ['POST'])
def success():
    if request.method == 'POST':
        #f = request.files['file']
        #f.save(f.filename)
        pt.pytesseract.tesseract_cmd = r'C:\Users\Mahendra\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
        imgs = cv2.imread('test2.png')
        img = imgs
        img = cv2.resize(imgs, None, fx=0.5, fy=0.5)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        adaptive_threshold = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 85, 35)

        text = pt.image_to_string(adaptive_threshold)

        ##Detecting characters
        hImg, wImg, _ = img.shape
        boxes = pt.image_to_boxes(adaptive_threshold)
        for b in boxes.splitlines():
            # print(b)
            b = b.split(' ')
            print(b)
            x, y, w, h = int(b[1]), int(b[2]), int(b[3]), int(b[4])
            cv2.rectangle(img, (x, hImg - y), (w, hImg - h), (0, 0, 255), 3)

        print(text)
        # print(boxes)

        cv2.imshow('adaptive thre', adaptive_threshold)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

'''
@app.route('/Wit', methods = ['POST'])
def filter_values(user_txt,token):
    client=Wit('NYQ2ZYOSKB3LVGXYDKLIDZAMZLKTCWPD')
    main_dict=client.message(f'{user_txt}')
    print(main_dict)
    ent_dict=main_dict['entities']
    keys=ent_dict.keys()
    li=""
    for key in keys:
        pro_list=ent_dict[key]
        val=pro_list[0]['body']
        li.append(val)
    return li
'''

@app.route("/answer", methods=["POST"])
def add_data():

    quest = request.json['user_quest']
    user_quest = quest
    #user_input = picture
    if not quest:
        return jsonify({"Error":"Invalid Question"})
    else:

        try:
            print("sdfdfdsf")
            Get_Answer = faqcol.find_one({"FAQ": {"$elemMatch": {"question": quest}}},
        {"FAQ.answer.$": 1, "FAQ.faqtype": "Returns", "FAQ._id": 1})
            answer = ""
            for i in Get_Answer["FAQ"]:
                answer = i['answer']
            if Get_Answer:
                return jsonify({"Answer": answer})
                # to create a new document to insert a new FQA
                faqcol.insert({"title": "userfaq", "user_quest": [{"question": "quest"}]})
                faqcol.update({"title": "userfaq"}, {"$push": {"user_quest": {"question": quest}}})


        except Exception as e:
            #print("Exception Mongo Query : ", e)
            Default_Answer = wikipedia.summary(user_quest, sentences = 3)

            return jsonify({"Answer": Default_Answer})
    return jsonify({"ERROR":"Something Went Wrong!!"})



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
    app.run(debug=True)