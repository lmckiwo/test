var http = require('http');

var fs = require('fs');
var data = fs.readFileSync("./status.json", "utf8");
var data1 = JSON.parse(data);

var server = http.createServer(function (req, res) {
  var html = buildHtml(req);

  res.writeHead(200, {
    'Content-Type': 'text/html',
    'Content-Length': html.length,
    'Expires': new Date().toUTCString()
  });
  res.end(html);
})

//server.setTimeout(10000, function(socket) {
//  console.log('destroyed') ;
//  socket.destroy()
//}) ;
server.listen(8080);

function buildHtml(req) {
  var header = '';
  var body = '';

  var data = fs.readFileSync("./status.json", "utf8");
  var data1 = JSON.parse(data);
  var hostfile = fs.readFileSync("./hosts.json", "utf8");
  var hostfile1 = JSON.parse(hostfile);
  var now = new Date();
  var date = now.getFullYear() + "/" + (now.getMonth() + 1) + "/" + now.getDate() ;
  var time = ("0" + now.getHours()).slice(-2) + ":" + ("0" + now.getMinutes()).slice(-2) + ":" + ("0" + now.getSeconds()).slice(-2) ;

  body = date + " " + time;
  body = body +
        "<br>version: 4.2" +
        "<font size='2'>" +
        "<h2>Legend</h2>" +
        // "<tr>" +
        // "<th>A</th>" +
        // "<th>B</th>" +
        // "</tr>" +
        "<table border='1'>" +
        "<tr>" +
        "<td bgcolor='red'>NOK</td>" +
        "<td bgcolor='green'>OK</td>" +
        "<td bgcolor='yellow'>Unknown</td>" +
        "</tr>" +
        "</table>" +
        // "<b>Status:</b><br>" +
        // "OK: ok<br>" +
        // "NOK: not ok<br>" +
        // "UNK: unknown<br>" +
        // "false: status not updated<br>" +
        "<p>" +
        "<b>UA:</b> if pingable via US = OK, else NOK<br>" +
        "<b>UC</b> if connected via US ssh  = OK, else NOK<br>" +
        "<b>CA:</b> if pingable via Canada = OK, else NOK<br>" +
        "<b>CC:</b> if connected via Canada ssh = OK, else NOK (will attemp only if US connection fails<br>" +
        "</p>" +
        "<p>If ssh is required, it will try US connection first by default.  If that fails, then it will try the Canadian IP.  Therefore, it is normal to see UC green and no color for CC.</p>" +
        "See <a href='http://mtl-cosma01q.cn.ca:3000/'>COSMA</a> for other alerts." +
         "<table border='1' >" +
//         "<col width='100'>" +
//         "<col width='120'>" +
//         "<col width='100'>" +
//         "<col width='75'>" +
         "<tr>" +
         "<th>Car</th>" +
         "<th>CN ID</th>" +
         "<th>Ensco Name</th>" +
         "<th>Ensco Unit</th>" +
         "<th>US IP</th>" +
         "<th>Can IP</th>" +
         "<th>Wi-fi</th>" +
         "</tr>";
var hostList = Object.keys(hostfile1) ;

for (var host2 in hostfile1) {
	if (host2 != "default") {
	body = body + "<tr><td>" + host2 + "</td>" ;
	body = body + "<td>" + hostfile1[host2]["config"]["CN-id"] + "</td>" ;
	body = body + "<td>" + hostfile1[host2]["config"]["ensco-name"] + "</td>" ;
	body = body + "<td>" + hostfile1[host2]["config"]["ensco-unit"] + "</td>" ;
  body = body + "<td>" + hostfile1[host2]["config"]["host-us"] + "</td>" ;
  body = body + "<td>" + hostfile1[host2]["config"]["host-can"] + "</td>" ;
  body = body + "<td>" + hostfile1[host2]["config"]["wifi"] + "</td>" ;
	body = body + "</tr>" ;
	}
}

//  header = "<meta http-equiv='refresh' content='60'><link rel='stylesheet' type='text/css' href='css/style.css' />" ;
  header = "<meta http-equiv='refresh' content='60'>" ;
  header = header +
	"<style>" +
	"table {" +
	"	  border: 1px solid;" +
	"	  margin: 12px;" +
	"	  padding: 3px;" +
	"}" +
	"caption {" +
	"	  font-weight: bold;" +
	"	  text-align: center;" +
	"	  border-style: solid;" +
	"	  border-width: 1px;" +
	"	  border-color: #666666;" +
	"}" +
        "</style>";
  header = header + "<h1>ATIC Status Monitor</h1><br>";

  body = body +
      "</table>" +
      "<h2>ATIC Cars</h2>" +
      "<div>" ;
//  body = "<table border='1'>" +
//         "<col width='100'>" +
//         "<col width='200'>" +
//         "<col width='100'>" +
//         "<col width='100'>" +
//         "<tr><th>Car</th><th>Node</th><th>Alive</th><th>Connected</th></tr>";

  var keys = Object.keys(data1) ;
  endOfTable = false;
  for (var host in data1) {
    var item = data1[host] ;
    if (item["config"]["active"] != "true") {
      continue
    }
    if (endOfTable) {
        body = body + "</table>" ;
        endOfTable = false;
     }
     body = body +
//	 "<h3>" + host + "</h3>" +
        "<table style='float: left' border='1'>" +
        "<caption>" + host + "</caption>" +
//         "<col width='100'>" +
//         "<col width='200'>" +
//         "<col width='100'>" +
//         "<col width='100'>" +
        "<tr>" +
//	 "<h3>" + host + "</h3>" +
//         "<th>Car</th>" +
        "<th>Node</th>" +
        "<th>UA</th>" +
        "<th>UC</th>" +
        "<th>CA</th>" +
        "<th>CC</th>" +
        "</tr>";

    for (var node in item["nodes"]) {
      endOfTable = true;
      var value = item["nodes"][node];

      body = body + "<tr>" +
 //                   "<td>" + host + "</td>" +
                    "<td>" + node + "</td>" ;

      if (typeof value["u_alive"] != "undefined") {
        if ((value['u_alive'] == "offline") || (value['u_alive'] == "NOK")) {
            body = body + "<td bgcolor='red'></td>" ;
        } else if ((value['u_alive'] == "online") || (value['u_alive'] == "OK")) {
            body = body + "<td bgcolor='green'></td>" ;
        }
        else {
          body = body + "<td></td>" ;
        }
      }


      if (typeof value["alive"] != "undefined") {
        if ((value['alive'] == "offline") || (value['alive'] == "NOK")) {
          body = body + "<td bgcolor='red'></td>" ;
        } else if ((value['alive'] == "online") || (value['alive'] == "OK")) {
          body = body + "<td bgcolor='green'></td>" ;
        }
        else if (value['alive'] == "UNK") {
          body = body + "<td bgcolor='yellow'></td>" ;
        }
        else {
          body = body + "<td></td>" ;
        }
      }


      if (typeof value["u_connected"] != "undefined") {
        if ((value["u_connected"] == "notConnected") || (value['u_connected'] == "NOK")) {
          body = body + "<td bgcolor='red'></td>" ;
        } else if ((value["u_connected"] == "connected") || (value['u_connected'] == "OK")) {
          body = body + "<td bgcolor='green'></td>" ;
        }
        else {
          body = body + "<td></td>" ;
        }
      } else {
        body = body + "<td></td>" ;
      }




      if (typeof value["c_alive"] != "undefined") {
        if ((value['c_alive'] == "offline") || (value['c_alive'] == "NOK")) {
            body = body + "<td bgcolor='red'></td>" ;
        } else if ((value['c_alive'] == "online") || (value['c_alive'] == "OK")) {
            body = body + "<td bgcolor='green'></td>" ;
        }
        else {
          body = body + "<td></td>" ;
        }
      } else {
        body = body + "<td></td>" ;
      }


      if (typeof value["c_connected"] != "undefined") {
        if ((value["c_connected"] == "notConnected") || (value['c_connected'] == "NOK")) {
          body = body + "<td bgcolor='red'></td>" ;
        } else if ((value["c_connected"] == "connected") || (value['c_connected'] == "OK")) {
          body = body + "<td bgcolor='green'></td>" ;
        }
        else {
          body = body + "<td></td>" ;
        }
      } else {
        body = body + "<td></td>" ;
      }


      body = body + "</tr>";
      //      body = body + key +  " " + value + "<br>" ;
    }
  }
    body = body + "</table>" ;
    body = body + "</div>";
  return '<!DOCTYPE html>'
       + '<html><head>' + header + '</head><body>' + body + '</body></html>';
}


//console.log(data1);
//var unique_id = data1[0].uniqueID;
//var order_id = data1[0].orderID;
//var order_date = data1[0].date;
//var cart_total = data1[0].cartTotal;
//
//document.getElementById("uid").innerHTML = unique_id;
//document.getElementById("oid").innerHTML = order_id;
//document.getElementById("date").innerHTML = order_date;
//document.getElementById("ctotal").innerHTML = cart_total;
