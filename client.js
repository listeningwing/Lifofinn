//#!/usr/bin/env node
//# -*- coding: utf-8 -*-

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
//  Model Context Protocol (MCP) client, the communication use normal TCP socket
//  with JSON format message, this protocol is independent of programming language,
//  although this prototype implemented with JavaScript, but user can scripting
//  LFF with other languages, such as Python, Ruby, Java, PHP, etc.  
//


const PORT = 42321;
const HOST = '127.0.0.1'; // Localhost
const accesscode = '***';

const net = require('net');
const client = new net.Socket();
const rawArray = [];


function makeRequst(msgtype, data, args){
    requst = `{"msgtype": "${msgtype}", "accesscode": "${accesscode}", "data": "${data}", "args": "${args}"}`
    return requst;
}


// send message to LFF, message must ends with '\r\n'
function sendRequst(sock, string){
    sock.write(string + '\r\n'); 
};



// Note: 
// LFF will automatically decode file path and text string that contains Unicode representations, 
// e.g., convert '\U3059\U3079\U3066\U306e\U4eba\U9593...' to 'すべての人間は...'.
function processRequsts(sock){
	const testString = "すべての人間は、生まれながらにして自由であり、かつ、尊厳と権利と について平等である。" + 
	     "มนุษย์ทั้งหลายเกิดมามีอิสระและเสมอภาคกันในเกียรติศักด[เกียรติศักดิ์]และสิทธิ" +
	     "모든 인간은 태어날 때부터 자유로우며 그 존엄과 권리에 있어 동등하다💄💋🌸☘️🛍️🎸👘***";
	     
    //while (true) {
          
          
          //1. isAccessible
          //2. isIgnoreFile
          //3. load root item in workspace
          //4. remove root item in workspace
	      let req = makeRequst('fileOperation', '/Users/yeung/Desktop/奈良桜/mcp_agent.js', '3');
          sendRequst(sock, req);
          
          
          // openFile, args=line number, optional
	      // let req = makeRequst('openFile', '/Users/yeung/Desktop/iOS/Makefile', '20');
          // sendRequst(sock, req);
           
          
          
          //1. show text in console
          //2. insert text at current cursor position. 
          //3. replace current selection with data.
          //4. append to end of current file.
          //5. insert text at the beginning of current file.
          //6. create a new temporary file with the text.
          
          
          //let req = makeRequst('textOperation', testString, '2');
          //sendRequst(sock, req);
          
          
          
          /*
          
          //show a message box
          req = makeRequst('showMessage', testString, '');
          sendRequst(sock, req);
          
          //show a yes/no selection box
          //req = makeRequst('showYesNoBox', 'title from js', '');
          //sendRequst(sock, req);
          */
          
          
          //***, placeholder, data length can't be 0
          //fetch path of currentFile and cursorLocation currentSelection
          // req = makeRequst('currentFileInfo', '***', '');
          // sendRequst(sock, req);
          
          //1. fetchRootUrls
          //2. cleanRootItems
          //3. fetchAccessibleList, note: accessible list + root urls = all accessible paths
          //4. listBookmarks
          //5. fetchRecentList
          //***, placeholder, data length can't be 0
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



// When data is received from the server (the echoed message)
client.on('data', (data) => {
	  let raw = data.toString(); //TODO: join data together and separate with '\r\n' into blocks
      // console.log(`raw from server: ${raw}`);
      
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
	        if(i == blocks.length) rawArray = [];
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
				  }
					  
				  
			  } catch (err) {
				  if(i == blocks.length)
				      rawArray.push(raw);
			  }
       } 
    
      //client.end(); // Close the connection after receiving the echo
});


// When the connection is closed
client.on('close', () => {
     console.log('Connection closed');
     //    
});


// Handle errors
client.on('error', (err) => {
    console.error('Client error:', err.message);
});


//console.log(process.argv);
const myArgs = process.argv.slice(2);
connect(HOST, myArgs[0]);


//1. directly edit this file in LFF.
//2. write a shell script with the following content.
//3. chmod +x /full/path/of/the/script, make the file executable. 
//4. run the script from within the editor.

/*
#!/bin/bash

cd ~/Desktop # or other place
# fetch full path of node
node = `which node`
node client.js 42321 

#42321: port number, LFF listening on, printed in console when start the server
*/



