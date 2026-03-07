<%
function AddXMLNode( DOMXML, Parent, Name, Value )
	Set AddXMLNode = AddXMLNodeEx( DOMXML, Parent, Name, Value, "" )
End Function

function AddXMLNodeEx( DOMXML, Parent, Name, Value, Namespace )
	dim objNode
	set objNode = DOMXML.createNode( 1, Name, Namespace)
	if Len(Value) <> 0 then
		objNode.text = Trim(Value)
	end if
	Parent.appendChild objNode
	set AddXMLNodeEx = objNode
End Function

function transformXML( XML, XSL ) 
	Dim objXML
	Dim objXSL
	
	Set objXML = getXMLDoc(XML)
	Set objXSL = getXMLDoc(XSL)
	If objXML.parseError <> 0 Then Response.Write reportParseError(objXML.parseError)
	If objXSL.parseError <> 0 Then Response.Write reportParseError(objXSL.parseError)

	transformXML = objXML.transformNode(objXSL)

End Function

Function getXMLDoc( XML )
	Dim objXML
	If IsObject(XML) Then 
		set objXML = XML
	Else
		Set objXML = Server.CreateObject("Microsoft.XMLDOM")
		
		If InStr(XML,"<") > 0 Then
			'This is a string because < is not valid in a filename
			objXML.LoadXML XML
		Else
			objXML.load(Server.MapPath(XML))
		End If
	End If
	
	Set getXMLDoc = objXML
End Function

Function RecordsetToXMLDoc( rs, NodeName )
	Dim objNodeCol, objNode, objXML, x
	
	set objXML = Server.CreateObject("Microsoft.XMLDOM")
	Set stylePI = objXML.createProcessingInstruction("xml:stylesheet","type=""text/xsl"" href=""bwseBACEN2CIDADE.xsl""")
	objXML.appendChild(stylePI)

	Set objNodeCol = AddXMLNode( objXML, objXML, "MsgsBACEN_TO_BCIDADE", "" )
	x = objNodeCol.setAttribute("xmlns","x-schema:bwseBACEN2CIDADE-schema.xml")
	
	Set objNode = AddXMLNode (objXML, objNodeCol, "Cabecalho1", "Mensagens Recebidas do BACEN")
	
	Set objNode = AddXMLNode (objXML, objNodeCol, "DataCorrente", now())
	
	while rs.EOF = False
		Set objNode = AddXMLNode( objXML, objNodeCol, NodeName, "" )
		for each x in rs.fields
			AddXMLNode objXML, objNode, x.Name, Trim(x.Value)
		Next
		rs.MoveNext
	wend
	objXml.save("c:\xxx.xml")
	Set RecordsetToXMLDoc = objXml
End Function

%>


<script language=javascript runat=server>
// Parse error formatting function
function reportParseError(error)
{
  var s = "";
  for (var i=1; i<error.linepos; i++) {
    s += " ";
  }
  r = "<font face=Verdana size=2><font size=4>XML Error loading '" + 
      error.url + "'</font>" +
      "<P><B>" + error.reason + 
      "</B></P></font>";
  if (error.line > 0)
    r += "<font size=3><XMP>" +
    "at line " + error.line + ", character " + error.linepos +
    "\n" + error.srcText +
    "\n" + s + "^" +
    "</XMP></font>";
  return r;
}

// Runtime error formatting function
function reportRuntimeError(exception)
{
  return "<font face=Verdana size=2><font size=4>XSL Runtime Error</font>" +
      "<P><B>" + exception.description + "</B></P></font>";
}
</script>

