import os
import socket
import subprocess


base="htdocs"

def phpObject(data):

    php_string = "$data = array(\n"     #create php array

    for v in data:
        php_string += f"    '{v[0]}' => '{v[1]}',\n"   #assignh the data values in to the createrd php array 

    php_string += ");"

    return php_string    #return php array



def webserver(host, port):
    temp_file_location = ''
    parameters = ''

    print(host)
    print(port)
    websocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)       #create socket for listen the request from recievd port / AF_INET and SOCK_STREAM use beacuse IPV4
    print(websocket)
    websocket.bind((host,port))                                        #bind both host and port to the websocket
    websocket.listen(5)                                                #we can take at most 5 connection together
    print("Server is running on http://"+host+":"+str(port))
    
    while True:  
        try:                           #use for get all reuset until recieve requests
            temp_file_location = ''
            parameters = ''

            connection, address = websocket.accept()        #websocket details assign to the connection, Then pass the port number of recieved request like wise 
            # print(connection)
            # print(connection.recv(1024))
            # print(connection.recv(1024).decode("utf-8").split("\r\n"))
            req_lines = connection.recv(4096).decode("utf-8").split("\r\n")        # "\r\n" sequence represents the end of a line or a header in the message
            print(req_lines)
            path =  req_lines[0].split(" ")[1]      #get the path using recievd Connection without 0 th index

            if 1 < len(path.split("?")):   # check "get" request has parameters 
                path,parameters = path.split("?")
                print(parameters)


            req_type = req_lines[0].split(" ")[0]        #get request method
            # print(req_lines)
            file_location = os.path.join(base, path.lstrip("/"))    #get the fil location using recieved request without '/' , file_location - 
            # print(os.path.commonpath([base, file_location]))
            if os.path.exists(file_location) and os.path.commonpath([base, file_location]) == base:      #check the filelocation is exist in the base or not
                # print(file_location)
                if os.path.isdir(file_location):               #check fileloaction is directory or not.then htdocs is directory , then it run index.php exsting in the htdocs directory
                    if os.path.exists(os.path.join(file_location,"index.php")):            
                        file_location = os.path.join(file_location,"index.php")
                    elif os.path.exists(os.path.join(file_location,"index.html")):
                        file_location = os.path.join(file_location,"index.html")
                    
                # print(file_location)
                if not(os.path.isdir(file_location)):           #if filelocation is not a directory
                    if file_location.endswith(".php"):

                        if req_type == "POST":

                            post_data = req_lines[req_lines.index('')+1].split("&")                     # find the index of empty string and add 1 and get that string value of that index and after split the value using &
                            post_data = list(map(lambda x: [ it for it in x.split("=")],post_data ))     ## create list like this [['n1', '23'], ['n2', '12'] after the split,
                            print(post_data)                                 #['n1', '23'], ['n2', '12']

                            # print(phpObj(post_data))

                            php_text = "<?php " + phpObject(post_data) + "\n $_POST = $data; ?> "   #call phpobj and pass the values of array and create new php file using given return php array and asighn value to the '$_POST'
                            # print(php_text)

                            with open(file_location, 'r') as php_file:              #now file_location is add.php , and read that file and assign it to  "php_code"
                                php_code = php_file.read()
                          
                            directory_path = os.path.dirname(file_location)               #get directory name (directory_path = htdocs)
                            file_name = "." + "temp" + "_" + os.path.basename(file_location)     #create new temparary php file as file_name
                            file_location = os.path.join(directory_path,file_name)                 #now join that created temp location and directory_path --> //localhost:2827/temp.php
                            temp_file_location = file_location


                            with open(file_location, 'w') as php_file:      #new file location is the location of temp, then write the php_text and php_code to new created temp location
                                php_file.write(php_text + php_code)            


                        if req_type == "GET" and parameters: 
                            get_data = parameters.split("&")
                            get_data = list(map(lambda x: [ it for it in x.split("=")], get_data))  

                            php_text = "<?php " + phpObject(get_data) + "\n $_GET = $data; ?> "       #create the php file

                            with open(file_location, 'r') as php_file:  
                                php_code = php_file.read()

                            directory_path = os.path.dirname(file_location)
                            file_name = "." + "temp" + "_" + os.path.basename(file_location)
                            file_location = os.path.join(directory_path, file_name)
                            temp_file_location = file_location

                            with open(file_location, 'w') as php_file:
                                php_file.write(php_text + php_code)


                            # print(post_data)

                        try:
                            output = subprocess.run(['php',file_location], capture_output=True, text=True, check=True)  #filelocation = temp  ,the we use "subprocess" to process new temp location and get the new adding result.
                            response = "HTTP/1.1 200 OK\r\n\r\n" + output.stdout                                        #give the finel output                
                        
                        except subprocess.CalledProcessError as e:
                            response = "HTTP/1.1 500 Internal Server Error\r\n\r\nInternal Server Error\n"  + e.stderr
                        
                        if temp_file_location:   # Delete temporary file 
                            try:
                                os.remove(temp_file_location)
                                print(f"File '{temp_file_location}' has been deleted.")
                            except OSError as e:
                                print(f"Error deleting file: {e}")

                    else:             #if recive file is not php
                        try:        
                            with open(file_location, "rb") as file:            #"rb" stands for "read binary." It's a file mode that indicates that you are opening the file in binary mode for reading
                                output = file.read()
                                response = "HTTP/1.1 200 OK\r\n\r\n" + output.decode("utf-8")        #decode("utf-8") method is used to convert the binary data in the output variable into a Unicode string.
                    
                        except Exception as e:
                            response = "HTTP/1.1 500 Internal Server Error\r\n\r\n" + str(e)
                else:
                    response = "HTTP/1.1 404 Not Found\r\n\r\nFile Not Found" 

            else:
                response = "HTTP/1.1 403 Forbidden\r\n\r\nForbidden"

            connection.sendall(response.encode("utf-8"))                    #encode and give the output

            connection.close()             #finely close the connection
        except:
            continue



host = "127.0.0.1"    #address 
port = 2728

webserver(host, port)


