<%@LANGUAGE=JScript%>
<html>
<head>
<title>Mensagem SPB</title>
</head><body>
<%

function attribute_walk(node) {

  for (k=1; k<indent; k++) {
    Response.Write("&nbsp;");
  }
  for  (m=0; m<node.attributes.length; m++){
   attrib = node.attributes.item(m);
   Response.Write("|--");
   Response.Write(attrib.nodeTypeString);
   Response.Write(":");
   Response.Write(attrib.name);
   Response.Write("--");
   Response.Write(attrib.nodeValue);
   Response.Write("<br />");
  }
} //end attribute_walk

function tree_walk(node) {

indent=indent+2;
for (current=0; current<node.childNodes.length; current++) {
  child=node.childNodes.item(current);
  for (j=1; j<indent; j++){
    Response.Write("&nbsp;");
  }
  Response.Write("|--");
  Response.Write(child.nodeTypeString);
  Response.Write("--");
  if (child.nodeType<3) {
    Response.Write(child.nodeName);
    Response.Write("<br />");
  }
  if (child.nodeType==1) { 
    if (child.attributes.length>0) {
      indent=indent+2;
      attribute_walk(child);
      indent=indent-2;
    }
  }
  if (child.hasChildNodes()) {
//store information so recursion is possible
    depthList[depth]=current;
    depth=depth+1;
    tree_walk(child);
//return from recursion
    depth=depth-1;
    current=depthList[depth];

  }else{
    Response.Write (child.text);
    Response.Write("<br />");
  }
}

  indent=indent-2;

}

//recursion-tracking variables
depth=0;
depthList=new Array();

indent=0;
xmlFile=new String();

xmlFile=Request.Form("selectl");
//xmlFile=""+xmlFile; 
//makes string clean for passing to MSXML
//xmlFile="<SPBDOC><BCMSG>teste</BCMSG></SPBDOC>";

xmlPresented=false;

var xmlDoc = new ActiveXObject("microsoft.xmldom");
xmlDoc.async = false;
xmlDoc.validateOnParse=false;
//xmlFile="http://127.0.0.1/ms/local.xml"
if ((xmlFile)) {
 xmlDoc.loadXML(xmlFile);
 if (xmlDoc.parseError.errorcode == null) {
  Response.Write("<h1>XML Parsing - Inicio</h1>");
  Response.Write("<pre>");
  tree_walk(xmlDoc);
  Response.Write("</pre>");
  Response.Write("<h1>XML Parsing - Fim</h1>");
  xmlPresented=true;
 }
}
if (xmlPresented==false){
%>
<h1>XML Parsing - Error</h1>
<% } %>
</body></html>
