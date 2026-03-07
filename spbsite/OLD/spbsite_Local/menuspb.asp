<% @LANGUAGE="JScript" %>
<%
	var sXml = "menuspb.xml"
	var sXsl = new String(Request.QueryString("xsl"));
	if ("undefined" == sXsl) sXsl = "menus.xsl"
	
	var oXmlDoc = Server.CreateObject("MICROSOFT.XMLDOM");
	var oXslDoc = Server.CreateObject("MICROSOFT.XMLDOM");
	oXmlDoc.async = false;
	oXslDoc.async = false;
	oXmlDoc.load(Server.MapPath(sXml));
	oXslDoc.load(Server.MapPath(sXsl));
	Response.Write(oXmlDoc.transformNode(oXslDoc));	
	oXmlDoc.async = false;
	oXslDoc.async = false;
	sXml = "stock-sorter.xml"
	sXsl = "stock-sorter.xsl"
	oXmlDoc.load(Server.MapPath(sXml));
	oXslDoc.load(Server.MapPath(sXsl));
	Response.Write(oXmlDoc.transformNode(oXslDoc));	
%>
