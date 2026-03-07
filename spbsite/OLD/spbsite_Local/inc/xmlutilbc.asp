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

function AddXMLNodeBinary( DOMXML, Parent, Name, Value )
	dim objNode
	dim I
	DIM strwrk
	set objNode = DOMXML.createNode( 1, Name, "")
	if Len(Value) <> 0 then
	   strwrk = ""
	   For I = 1 To Len(Value)
		   strwrk = Hex(Mid(Value,i,1))
	   Next
	   objNode.text = strwrk
	end if
	Parent.appendChild objNode
	set AddXMLNodeBinary = objNode
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

Function RecordsetToXMLDoc( rs, Cabec, xslpgm )
	Dim objNodeCol, objNode, objXML, x, PrcInstr, Schema
	
	PrcInstr = "type=" & chr(34) & "text/xsl" & chr(34) & " href=" & chr(34) & xslpgm & ".xsl" & chr(34)
	
	set objXML = Server.CreateObject("Microsoft.XMLDOM")
	Set stylePI = objXML.createProcessingInstruction("xml:stylesheet",PrcInstr)
	objXML.appendChild(stylePI)

	Set objNodeCol = AddXMLNode( objXML, objXML, "MainTag" , "" )
	
	Set objNode = AddXMLNode (objXML, objNodeCol, "Cabecalho1", Cabec)
	
	Set objNode = AddXMLNode (objXML, objNodeCol, "DataCorrente", now())
	
	while rs.EOF = False
		Set objNode = AddXMLNode( objXML, objNodeCol, "EntryTag", "" )
		for each x in rs.fields
			if x.Type = 135 then			' timestamp
				Ano = year(x.Value)
				Mes = month(x.Value)
				if Mes < 10 then Mes = "0" & Mes
				Dia = day(x.Value)
				if Dia < 10 then Dia = "0" & Dia
				Horas = hour(x.Value)
				if Horas < 10 then Horas = "0" & Horas
				Minutos = minute(x.Value)
				if Minutos < 10 then Minutos = "0" & Minutos
				Segundos = second(x.Value)
				if Segundos < 10 then Segundos = "0" & Segundos
				AddXMLNode objXML, objNode, x.Name, Ano & Mes & Dia & Horas & Minutos & Segundos
			else
'				Response.Write(x.name & " " & x.Type)
				if x.Type <> 128 then
					AddXMLNode objXML, objNode, x.Name, Trim(x.Value)
'				else
'					AddXMLNodeBinary objXML, objNode, x.Name, x.Value
				end if
			end if
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

