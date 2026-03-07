<HTML>
	<XML id="menuspb" src="menuspb.xml"></XML>
	<XML id="historico" src="historico.xml"></XML>
	<XML id="menuxsl" src="menus.xsl"></XML>
	<XML id="histxsl" src="historico.xsl"></XML>
	<HEAD>
	<LINK REL="stylesheet" TYPE="text/css" HREF="menus.css" />
	<TITLE>Menu <xsl:value-of select="TOPICLIST/@TYPE" /></TITLE>
	<SCRIPT LANGUAGE="JScript" SRC="menus.js"></SCRIPT>
	</HEAD>
<SCRIPT language="JavaScript" for="window" event="onload">
  cell1.innerHTML = menuspb.transformNode(menuxsl.XMLDocument)
  cell2.innerHTML = historico.transformNode(histxsl.XMLDocument)
</SCRIPT>
	
<BODY>
<h1 id="cell1"></h1>
<P>Source file "historico.xml"</P>
<h1 id="cell2"></h1>


 <script language="JavaScript">
    document.write("Este é um JavaScript!<BR><BR><BR><BR>");
 </script>

<TABLE border="2"> 
<TR><TD><B>Server Variable</B></TD><TD><B>Value</B></TD></TR>
<% For Each name In Request.ServerVariables %> 
<TR><TD> <%= name %> </TD><TD>  <%= Request.ServerVariables(name) %> </TD></TR>
<% Next %> 
<TR><TD> A </TD><TD>  <%= Application("A") %> </TD></TR>
<TR><TD> S </TD><TD>  <%= Application("S") %> </TD></TR>
</TABLE>
<% 
   Response.Write("<P>VARIAVEIS DO FORMULARIO:<br>")
   Response.Write("-------------------------------<br>")
   For Each Key in Request.Form
    Response.Write( Key & " = " & Request.Form(Key) & "<br>")
   Next
   
   Response.Write("<P>VARIAVEIS QUERY STRING:<br>")
   Response.Write("------------------------------<br>")
   For Each Key in Request.QueryString
    Response.Write( Key & " = " & Request.QueryString(Key) & "<br>")
   Next
   
   Response.Write("<P>VARIAVEIS TIPO COOKIE:<br>")
   Response.Write("-----------------------------<br>")
   For Each Key in Request.Cookies
    Response.Write( Key & " = " & Request.Cookies(Key) & "<br>")
   Next
   
   %>
   

</BODY>
</HTML>