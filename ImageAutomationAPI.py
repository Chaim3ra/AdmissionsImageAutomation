from flask import Flask, request, render_template, Response
from flask_restful import Resource, Api
from PIL import Image
import os
from werkzeug import secure_filename
from functools import wraps
import cv2
import matplotlib.pyplot as plt
import math

#
#Author : Chaitanya Agarwal
#created on : 22/01/2019
#

app=Flask(__name__)
app.config['RAW_IMAGES'] = os.path.join('static', 'RAW_IMAGES')
app.config['CROPPED_IMAGES'] = os.path.join('static', 'CROPPED_IMAGES')
app.config['PROCESSED_IMAGES'] = os.path.join('static', 'PROCESSED_IMAGES')

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'pass'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def rgb_to_hsv(r, g, b):
    maxc = max(r, g, b)
    minc = min(r, g, b)
    v = maxc
    if minc == maxc:
        return 0.0, 0.0, v
    s = (maxc-minc) / maxc
    rc = (maxc-r) / (maxc-minc)
    gc = (maxc-g) / (maxc-minc)
    bc = (maxc-b) / (maxc-minc)
    if r == maxc:
        h = bc-gc
    elif g == maxc:
        h = 2.0+rc-bc
    else:
        h = 4.0+gc-rc
    h = (h/6.0) % 1.0
    return h, s, v

GREEN_RANGE_MIN_HSV = (80, 100, 100)
GREEN_RANGE_MAX_HSV = (185, 255, 255)

def facecrop(image):
    
    facedata = '/anaconda3/lib/python3.6/site-packages/cv2/data/haarcascade_frontalface_alt.xml'
    cascade = cv2.CascadeClassifier(facedata)

    img = cv2.imread(image)

    minisize = (img.shape[1],img.shape[0])
    miniframe = cv2.resize(img, minisize)

    faces = cascade.detectMultiScale(miniframe)

    for f in faces:
        x, y, w, h = [ v for v in f ]
        #cv2.rectangle(img, (x,y), (x+w,y+h), (255,255,255,0))

        sub_face = img[y-math.floor(0.50*h):y+h+math.floor(0.40*h), x-math.floor(0.20*w):x+w+math.floor(0.20*w)]
        fname, ext = os.path.splitext(image)
        #sub_face.save(os.path.join(app.config['CROPPED_IMAGES'], fname+ext))
        cv2.imwrite(fname+ext, sub_face)




    return 



@app.route('/')
@requires_auth
def index():
   return render_template('ImagePreview.html')

@app.route('/count')
def countImages():
    path1, dirs1, files_raw = next(os.walk(app.config['RAW_IMAGES']))
    path2, dirs2, files_processed = next(os.walk(app.config['PROCESSED_IMAGES']))
    raw_count = len(files_raw)-1
    processed_count=len(files_processed)-1
    #file_count=""+file_count+""
    return "Raw images = "+str(raw_count)+"\nProcessed images= "+str(processed_count)

@app.route('/upload', methods = ['GET', 'POST'])
def compute():
    if request.method == 'POST':
        img=request.files['file']
        img1=img
        filename=secure_filename(img.filename)
        img.save(os.path.join(app.config['CROPPED_IMAGES'], filename))
        img1.save(os.path.join(app.config['RAW_IMAGES'], secure_filename(img1.filename)))
        facecrop(os.path.join(app.config['CROPPED_IMAGES'], filename))
        im=Image.open(os.path.join(app.config['CROPPED_IMAGES'], filename))
        im=im.convert('RGB')
        pix=im.load()
        width,height=im.size
        for x in range(width):
            for y in range(height):
                r, g, b = pix[x, y]
                h_ratio, s_ratio, v_ratio = rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
                h, s, v = (h_ratio * 360, s_ratio * 255, v_ratio * 255)
                min_h, min_s, min_v = GREEN_RANGE_MIN_HSV
                max_h, max_s, max_v = GREEN_RANGE_MAX_HSV
                if min_h <= h <= max_h and min_s <= s <= max_s and min_v <= v <= max_v:
                    pix[x, y] = (255, 255, 255,1)
        im.save(os.path.join(app.config['PROCESSED_IMAGES'], filename))
        before=os.path.join(app.config['CROPPED_IMAGES'], filename)
        after=os.path.join(app.config['PROCESSED_IMAGES'], filename)
    return render_template('ImagePreview.html', user_image = before, user_image2= after)
    return "success!"
    return redirect('/')






#api.add_resource(test, "/")
##api.add_resource(upload,"/upload")

if __name__=='__main__':
	app.run(debug=True)