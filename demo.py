import streamlit as st
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc, service_pb2, resources_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2
from clarifai.client.auth.helper import ClarifaiAuthHelper
from clarifai.client import create_stub
from clarifai.modules.css import ClarifaiStreamlitCSS
from clarifai.urls.helper import ClarifaiUrlHelper
from clarifai_grpc.grpc.api import resources_pb2, service_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2
from google.protobuf import json_format
import cv2
import shutil
import numpy as np
import io
from google.protobuf.json_format import MessageToDict
import requests
from PIL import Image
from io import BytesIO
import os
import requests
from streamlit.runtime.uploaded_file_manager import UploadedFile

###############################################################################
####    Main Application Setup                                             ####
###############################################################################

# Your PAT (Personal Access Token) can be found in the portal under Authentification
PAT = 'f4436e29bdc245ca83de8e9a3f1a4499'
# User and App IDs
USER_ID = 'clarifaijeff'
APP_ID = 'blurred-documents-demo'
#our model needs to be designated, with version
MODEL_ID = 'blurrydarkclear-tl'
MODEL_VERSION_ID = '20ba660b270d4a1fa57bec97afb87b3d'

#basic formatting
st.set_page_config(layout="wide")


#set the page title
st.title("Document Upload Checker")

#build our gRPC endpoints and handle authentication and user data
channel = ClarifaiChannel.get_grpc_channel()
stub = service_pb2_grpc.V2Stub(channel)
metadata = (('authorization', 'Key ' + PAT),)
userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)

if 'upButton' not in st.session_state:
    st.session_state.disabled = True 

###############################################################################
####    Function Definitions                                            
###############################################################################

def make_inference_req(file_bytes):
    post_model_outputs_response = stub.PostModelOutputs(
        service_pb2.PostModelOutputsRequest(
            user_app_id=userDataObject,  # The userDataObject is created in the overview and is required when using a PAT
            model_id=MODEL_ID,
            version_id=MODEL_VERSION_ID,  # This is optional. Defaults to the latest model version
            inputs=[
                resources_pb2.Input(
                    data=resources_pb2.Data(
                        image=resources_pb2.Image(
                            base64=file_bytes
                        )
                    )
                )
            ]
        ),
        metadata=metadata
    )
    return post_model_outputs_response



###############################################################################
####    Main Application Execution                                            
###############################################################################




if __name__ == "__main__":
    ClarifaiStreamlitCSS.insert_default_css(st)
    
    #present a file upload modal for the user to add their driver's license / etc
    #uploaded_file = st.file_uploader('Upload Document:') 

    #present a mobile phone camera interface for image capture
    uploaded_file = st.camera_input("take photo")

    #preprocessing for the uploaded document
    if uploaded_file is not None:
        #read the uploaded file and store it in file_bytes variable
        file_bytes = uploaded_file.read()
        image = Image.open(io.BytesIO(file_bytes))
        st.image(image, caption='Uploaded Document', width=250)

        inference_results = make_inference_req(file_bytes)
        if inference_results.status.code != status_code_pb2.SUCCESS:
            # failure detected, push errors to the user and exit.
            print(inference_results.status)
            print("Post workflow results failed, status: " + inference_results.status.description)

        output = (inference_results.outputs[0])
        ###################################################################
        ####    Debug Block
        ####    Uncomment to see the concepts listed with their confidence
        print(output)
        ###################################################################
        for concept in output.data.concepts:
            if concept.name == 'blurry':
                if concept.value > .4:
                    st.write('The image is blurry, confidence ', concept.value)
            if concept.name == 'dark':
                if concept.value > .4:
                    st.write('The image is dark, confidence ', concept.value)
            if concept.name == 'clear':
                if concept.value > .1:
                    st.write('The image is clear!, confidence ', concept.value)
                    st.session_state.disabled = False
            
upload_button = st.button('Upload', key='upButton', disabled=st.session_state.disabled)

#st.write(upload_button)
            ###################################################################
            ####    Debug Block
            ####    Uncomment to see the concepts listed with their confidence
            ###################################################################

            #st.write("%s %.2f" % (concept.name, concept.value))


#I'm going to comment this block out, and then change from URL to base64 for the image.
#post_model_outputs_response = stub.PostModelOutputs(
#   service_pb2.PostModelOutputsRequest(
#        user_app_id=userDataObject,  # The userDataObject is created in the overview and is required when using a PAT
#        model_id=MODEL_ID,
#        version_id=MODEL_VERSION_ID,  # This is optional. Defaults to the latest model version
#        inputs=[
#            resources_pb2.Input(
#                data=resources_pb2.Data(
#                    image=resources_pb2.Image(
#                        url=IMAGE_URL
#                    )
#                )
#            )
#        ]
#    ),
#    metadata=metadata
#)
#if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
#    print(post_model_outputs_response.status)
#    raise Exception("Post model outputs failed, status: " + post_model_outputs_response.status.description)

# Since we have one input, one output will exist here
#output = post_model_outputs_response.outputs[0]

#print("Predicted concepts:")
#for concept in output.data.concepts:
#    print("%s %.2f" % (concept.name, concept.value))

# Uncomment this line to print the full Response JSON
#print(output)

