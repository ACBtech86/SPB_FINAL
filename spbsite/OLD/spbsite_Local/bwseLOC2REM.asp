<% Response.ContentType = "text/xml" %>
<!-- #INCLUDE file="connect.asp" -->
<!-- #INCLUDE FILE="inc/xmlutilbc.asp" -->

<%
  	Dim objXMLx
  	Dim oXslDoc
  	Dim Cabec
  	Dim xslpgm
  	Dim xslapp
	Dim Tabela
	
	xslapp = "bwseLOC2REM"
	xslpgm = xslapp & ".xsl"
	Cabec = "Mensagens Enviadas para o SPB"
	Tabela = "SPB_LOCAL_TO_BACEN SPB_LOCAL_TO_SELIC "
		
	set oXslDoc = getXMLDoc(xslpgm)
 
   	Set objXMLx = RecordsetToXMLDoc(GetRecordset(Tabela), Cabec, xslapp)

 	objXMLx.transformNode oXslDoc
 	
 	Response.Write(objXMLx.xml)

%>

<% 
Function GetRecordset(Tabela)
	Dim cnn
    Dim query
    
    Set cnn = Server.CreateObject("adodb.connection")
    cnn.Open strDBConnection
    query = "select * from " & Tabela & " ORDER BY DB_DATETIME"
	Set GetRecordset = cnn.Execute(query)

End Function 
%>   

	