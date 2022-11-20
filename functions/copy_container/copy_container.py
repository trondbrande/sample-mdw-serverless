import logging
import azure.functions as func
from azure.storage.blob import BlobServiceClient
import io
import uuid

def validate_input(source_container, target_container, source_cs, target_cs ):
    '''
    Minimal input validation
    '''
    if (source_container and target_container and target_cs and source_cs):
        return True
    else:
        logging.critical('fatal: copy container function invalid input payload') 
        return False

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('copy container processed a request.')
    '''
    The function based on the source and target containers would copy from source to target
    Note, in case the size of the blob is zero, it will not be copied. This is done to allow skipping of directories.
    The json payload this function assume to have in the POST include:    
    - file_container - the container of the file
    - target_container - usualy will be 'silver'
    - target_path - the directory containing the splited files (../silver/xyz/qwe/y=2022/m=08/)
    - source_cs - the connection string to the source container/folder
    - target_cs - the connection string to the target folder
    - the function will place the data per day in a file under the folder d=xx with guid.parquet name
    '''      
    try:
        req_body = req.get_json()
        logging.info('copy function got payload.')
    except ValueError:
        logging.critical('fatal: copy container function called without payload.')
        pass
    else:        
        source_container = req_body.get('source_container')
        target_container = req_body.get('target_container')        
        source_cs = req_body.get('source_cs')
        target_cs = req_body.get('target_cs')
        #getting the account name from the cs, this is needed to allow for copy_from_url.
        _splitted = source_cs.split(';')
        acct_name = _splitted[1].split('=')[1]


    if validate_input(source_container,target_container,target_cs,source_cs):
        blob_service_source = BlobServiceClient.from_connection_string(source_cs)
        blob_service_target = BlobServiceClient.from_connection_string(target_cs)

        source_container_client = blob_service_source.get_container_client(container = source_container)
        target_container_client = blob_service_target.get_container_client(container = target_container) 
        source_details = source_container_client.get_account_information()
        print(f"these are the details:{source_details}")
        blob_list = source_container_client.list_blobs()
        for blob in blob_list:
            # checking this is not an empty file or a directory
            if blob.size > 0:
                # getting a handle for the target blob
                target_blob_client = target_container_client.get_blob_client(blob.name)                
                sourceBlobUrl = (f"https://{acct_name}.blob.core.windows.net/{source_container}/{blob.name}")
                print(sourceBlobUrl)
                # using the copy_from allows the calling function not to wait for compeletion, the response for this call is 202
                target_blob_client.start_copy_from_url(sourceBlobUrl)
        return func.HttpResponse(f"Copied files from source: {source_container} to target:{target_container}")
    else: 
        return func.HttpResponse("Invalid inputs", status_code=500)
    
