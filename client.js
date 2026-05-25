#!/usr/bin/env node


/*
#    __   _ ___     ____
#   / /  (_) _/__  / _(_)__  ___
#  / /__/ / _/ _ \/ _/ / _ \/ _ \
# /____/_/_/ \___/_//_/_//_/_//_/
# The ultra small code editor.
#
*/


//  Purpose: 
//  this file provide protocol for client side scripting Lifofinn (LFF) that  
//  can be easily integrated with AI code assistant, CLI chat bot, and 
//  Model Context Protocol (MCP) client, the communication use normal TCP based
//  JSON format message, this protocol is independent of programming language,
//  although this prototype implemented with JavaScript, but user can scripting
//  LFF with other languages, such as Python, Ruby, Java, PHP, etc.  
//


const PORT = 42321;
const HOST = '127.0.0.1'; // Localhost
const accesscode = '***';

const fs = require('fs');
const net = require('net');
let client = new net.Socket();
let rawArray = [];
let timer = null;
let connectionClosed = false;

function makeRequst(msgtype, data, args){
    requst = `{"msgtype": "${msgtype}", "accesscode": "${accesscode}", "data": "${data}", "args": "${args}"}`
    return requst;
}


function makeWebRequst(msgtype, mimetype, encoding, baseurl, data){
    requst = `{"msgtype": "${msgtype}", "accesscode": "${accesscode}", ` +
    `"MIMEType": "${mimetype}", "Encoding": "${encoding}", "BaseURL": "${baseurl}", "data": "${data}",  }`
    return requst;
}


// send message to LFF, message must ends with '\r\n'
function sendRequst(sock, string){
	if(connectionClosed) {
	    client = new net.Socket();
	    sock = client;
	}
    sock.write(string + '\r\n');
};

function destroyTimer(timer){
    if (timer !== null) {
       clearTimeout(timer);
       timer = null;
    }
};



// Note:
// a. LFF will automatically decode file path and text string that contains Unicode representations,
//    e.g., convert '\U3059\U3079\U3066\U306e\U4eba\U9593...' to 'すべての人間は...'.
// b. Some data field in message from LFF was encoded with base64.
function processRequsts(sock){
	const testString = "すべての人間は、生まれながらにして自由であり、かつ、尊厳と権利と について平等である。" + 
	     "มนุษย์ทั้งหลายเกิดมามีอิสระและเสมอภาคกันในเกียรติศักด[เกียรติศักดิ์]และสิทธิ" +
	     "모든 인간은 태어날 때부터 자유로우며 그 존엄과 권리에 있어 동등하다💄💋🌸☘️🛍️🎸👘***";
	     
    //while (true) {
          
          
          //1. isAccessible
          //2. isIgnoreFile
          //3. load root item in workspace
          //4. remove root item in workspace
	      //let req = makeRequst('fileOperation', '/Users/yeung/Desktop/奈良桜/mcp_agent.js', '3');
          //sendRequst(sock, req);
          
          
          // open file in the text editor, args=line number, optional
          // *** Note: args = -1, goto end of the file
	      // let req = makeRequst('openFile', '/Users/yeung/Desktop/iOS/Makefile', '20');
          // sendRequst(sock, req);

          // open local file or remote url associated resource in the built-in browser.
          //*** Note: just input full path of the file for local file
          //let req = makeRequst('openURL', 'https://bing.com', '');
          //let req = makeRequst('openURL', 'https://google.com', '');
          //let req = makeRequst('openURL', 'https://stackoverflow.com', '');
          //let req = makeRequst('openURL', '/Users/yeung/Desktop/small_software_manifesto.txt', '');
          //sendRequst(sock, req);
          
          
          //1. show the text in console.
          //2. insert the text at current cursor position.
          //3. replace current selection with the text.
          //4. append the text to end of current file.
          //5. insert the text at the beginning of current file.
          //6. create a new temporary file with the text.
          //let req = makeRequst('textOperation', testString, '1');
          //sendRequst(sock, req);
          

          //instantly show program generated raw data of graph or other web content in the built-in browser.
          //MIMEType: (e.g., "text/plain", "text/html", "image/bmp", "image/jpeg", "image/png", "application/pdf",  "image/svg+xml")
          //    Word: application/msword (.doc) Excel: application/vnd.ms-excel (.xls) PowerPoint: application/vnd.ms-powerpoint (.ppt)
          //Encoding: text encoding, usually "utf-8" or "utf-16", be empty for non-text data.
          //BaseURL:  a valid URL required, default is "http://localhost".
          //Note:
          //***  a. "Encoding" must be empty to indicate the data is base64 encoded binary data.
          //***  b. if a file already saved on disk (local files), more reliable way is to use "openURL".
          const bitmap = fs.readFileSync('sad.webp'); // Read binary data
          // Convert binary data to base64 encoded string
          const base64Image = Buffer.from(bitmap).toString('base64');
          let req = makeWebRequst('showInBrowser', 'image/webp', '', '', base64Image);
          sendRequst(sock, req);

    
          //show a message box
          //req = makeRequst('showMessage', testString, '');
          //sendRequst(sock, req);
          
/*
          //show a yes/no selection box
           req = makeRequst('showYesNoBox', 'title from js', '');
           sendRequst(sock, req);
           
           destroyTimer (timer);
           timer = setTimeout(() => {
                 console.log("timer out, no response from LFF.");
                 destroyTimer(timer);
                 client.end(); // end this time session
                 
           }, 5000);
           // "Destroy" the timer before it triggers
           //destroyTimer(timer);
    
*/

          
          // a. ***, placeholder, data length can't be 0
          // b. current selection encoded with base64
          // fetch path of current file, cursor location, and current selection
          // req = makeRequst('currentFileInfo', '***', '');
          // sendRequst(sock, req);
    
          
          //1. fetchRootUrls
          //2. cleanRootItems
          //3. fetchAccessibleList, note: accessible list + root urls = all accessible paths
          //4. listBookmarks
          //5. fetchRecentList
          //Note:
          //a. ***, placeholder, data length can't be 0
          //b. please decode "line brief" with base64 when listBookmarks()
          //let req = makeRequst('dbOperation', '***', '5');
          //  sendRequst(sock, req);
          

          
	     
    //}
};



function connect(host, port){
	client.connect(port, host, () => {
		 console.log('connected to Lifofinn.\n');
		 processRequsts(client);
	});
};


function onConnectionClosed(){
    if(connectionClosed) return;
    connectionClosed = true;
    client = null;
    console.log('Connection closed');
};


// When data is received from the server, each block ends with '\r\n'
client.on('data', (data) => {
      //TODO: join data together and separate into blocks
	  let raw = data.toString();
      // console.log(`raw from server: ${raw}`);
      if(raw.length == 0) return;
      
      let text;
      if(rawArray.length > 0){
          rawArray.push(raw);
          text = rawArray.join("");
	  }else{
		  text = raw;
	  }
	  //console.log(`text: ${text}`);

      const blocks = text.split('\r\n'); 
      for (let i = 0; i < blocks.length; i++) {
	        let jsonString = blocks[i];
	        if(i == blocks.length-2) rawArray = []; //last block
	        try {
				  const object = JSON.parse(jsonString);
				  console.log(`return message: ${blocks}`);
				  console.log('\n\n');
				  if(object.msgtype === "showMessage"){
					   console.log('showMessage returned.');
					   let req = makeRequst('showYesNoBox', 'Title from JS', '');
					   sendRequst(client, req);
				  }
				  else if(object.msgtype === "dbOperation"){
					   if(object.args === "4")
					      client.end(); // end this time session
				  }else if(object.msgtype === "showYesNoBox"){
					   destroyTimer (timer);
					   console.log(`LFF return: ${object.result}`);
					   client.end();
				  }
           
           
			  } catch (err) {
                  if(i == blocks.length-2){
                       rawArray.push(raw);
                  }
			  }
       } 
    
      //client.end(); // Close the connection after receiving the echo
});


// When the connection is closed
client.on('close', () => {
    onConnectionClosed();
});

client.on('end', () => {
    onConnectionClosed();
});


// Handle errors
client.on('error', (err) => {
    console.error('Client error:', err.message);
});


const myArgs = process.argv.slice(2);
if(myArgs.length > 0) connect(HOST, myArgs[0]);
else console.log('please provide the port number.');


//1. directly edit this file in LFF.
//2. write a shell script with the following content.
//3. chmod +x /full/path/of/the/script, make the file executable.
//4. LFF: Command  → Start JSON Server
//5a. run this script from within the editor by directly call connect().
//5b. run shell script from command line.

/*
#!/bin/bash

cd ~/Desktop/Test # or other place
# fetch full path of node
node = `which node`
node client.js 42321 # tested with node v20
42321: port number, LFF listening on, printed in console when start the server.
*/



