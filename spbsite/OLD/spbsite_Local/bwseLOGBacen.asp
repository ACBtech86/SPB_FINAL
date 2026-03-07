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
	
	xslapp = "bwseSPBLOG"
	xslpgm = xslapp & ".xsl"
	Cabec = "Log do Sistema SPB Banco Central"
	Tabela = "SPB_LOG_BACEN"
		
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
    query = "select * from " & Tabela
	Set GetRecordset = cnn.Execute(query)

End Function 
%>   

	