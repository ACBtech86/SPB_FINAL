<?xml version="1.0"?>

<!-- Note that this stylesheet relies on the XMLDocument and XSLDocument properties and thus
     only works when browsing XML -->
  
<xsl:stylesheet xmlns:xsl="http://www.w3.org/TR/WD-xsl">
  <xsl:template match="/">
     <STYLE>
          BODY {margin:0}
          .fntPagina {font:8pt Verdana; background-color:white; color:blue}
          .fntLeftPag {font:8pt Times New Roman; background-color:white; color:black}
          H1 {font:bold 14pt Verdana; width:100%; margin-top:1em;color:gray}
          .fntfntLinhaTab {font:4pt Verdana; border-bottom:1px solid #CC88CC}
          .fntCabecTab {font:italic 6pt Verdana; cursor:hand; padding:2px; border:2px outset gray}
          .Cor_Erro {background-color:#FFBBBB;}		<!-- Vermelho -->
          .Cor_Aviso {background-color:#FFFFBB;}	<!-- Verde    -->
          .Cor_Normal {background-color:#DDFFDD;}	<!-- Verde    -->

		<!-- (N)ormal, (E)rro - Vermelho e (R)eport - Amarelo  -->
        </STYLE>  
      
      <SCRIPT><xsl:comment><![CDATA[

        function Classifica(coluna)
        {
          sortField.value = coluna;
          <!-- set cursor to watch here? -->
          listing.innerHTML = source.documentElement.transformNode(stylesheet);
        }

      ]]></xsl:comment></SCRIPT>

      <SCRIPT for="window" event="onload"><xsl:comment><![CDATA[
          
          stylesheet = document.XSLDocument;
          source = document.XMLDocument;
          sortField = document.XSLDocument.selectSingleNode("//@order-by");
      ]]></xsl:comment></SCRIPT>
      
        <TABLE width="100%" cellspacing="0">
          <TR>
            <TD class="fntPagina"/>
            <TD class="fntPagina">
                <H1><xsl:value-of select="MainTag/Cabecalho1"/>
                em <xsl:value-of select="MainTag/DataCorrente"/></H1>
            </TD>
          </TR>
          <TR>
            <TD class="fntLeftPag" width="120" valign="top">
              <P><xsl:eval>totalGerS(this)</xsl:eval></P>
              <P><xsl:eval>totalGerN(this)</xsl:eval></P>
              <P><xsl:eval>totalConS(this)</xsl:eval></P>
              <P><xsl:eval>totalConN(this)</xsl:eval></P>
              <P><B><xsl:eval>totalTrafego(this)</xsl:eval></B></P>
              <P>                                               </P>
              <P>Clique no cabecalho da coluna para classificar.</P>
              <P>                                               </P>
              <P>Linhas com ERRO estao representadas em VERMELHO,
              as indicadas em VERDE indicam atencao.</P>
            </TD>
            <TD class="fntPagina" valign="top">
               <DIV id="listing"><xsl:apply-templates select="MainTag"/></DIV>
            </TD>
          </TR>
        </TABLE>    
  </xsl:template>
  
  <xsl:template match="MainTag">

    <TABLE STYLE="font:8pt Verdana; background-color:white">
      
      <TCabecalho>      
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('CNPJ')">CNPJ</DIV></TD>
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('NOME_CNPJ')">NOME_CNPJ</DIV></TD>
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('MSG_SEQ')">MSG_SEQ</DIV></TD>
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('STATUS_GERAL')">STATUS_GERAL</DIV></TD>
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('STATUS_CONECT')">STATUS_CONECT</DIV></TD>
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('DTHR_CONECT')">DTHR_CONECT</DIV></TD>
		<TD width="80"><DIV class="fntCabecTab" onClick="Classifica('DTHR_DESCON')">DTHR_DESCON</DIV></TD>
		<TD width="80"><DIV class="fntCabecTab" onClick="Classifica('DTHR_ECO')">DTHR_ECO</DIV></TD>
		<TD width="80"><DIV class="fntCabecTab" onClick="Classifica('ULTMSG')">ULTMSG</DIV></TD>
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('DTHR_ULTMSG')">DTHR_ULTMSG</DIV></TD>
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('CERTIFICADORA')">CERTIFICADORA</DIV></TD>
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('NUM_CERTIFICADO')">NUM_CERTIFICADO</DIV></TD>
      </TCabecalho>
      
      <xsl:for-each select="EntryTag" order-by="NOME_CNPJ">
        <TR>
 		  <xsl:choose>
		    <xsl:when test="STATUS_GERAL[. $eq$ 'N']">
                <xsl:attribute name="class">Cor_Erro</xsl:attribute>
		    </xsl:when>
		    <xsl:when test="STATUS_CONECT[. $eq$ 'N']">
                <xsl:attribute name="class">Cor_Erro</xsl:attribute>
		    </xsl:when>

		    <xsl:otherwise>
                <xsl:attribute name="class">Cor_Normal</xsl:attribute>
	        </xsl:otherwise>

		  </xsl:choose>

          <TD><DIV class="fntLinhaTab"><xsl:value-of select="CNPJ"/></DIV></TD>  
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="NOME_CNPJ"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="MSG_SEQ"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="STATUS_GERAL"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="STATUS_CONECT"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:apply-templates select="DTHR_CONECT"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:apply-templates select="DTHR_DESCON"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:apply-templates select="DTHR_ECO"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="ULTMSG"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:apply-templates select="DTHR_ULTMSG"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="CERTIFICADORA"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="NUM_CERTIFICADO"/></DIV></TD>    
        </TR>
      </xsl:for-each>
    </TABLE>
  </xsl:template>
  
  <xsl:template match="DTHR_CONECT | DTHR_DESCON | DTHR_ECO | DTHR_ULTMSG">
    <xsl:eval>FmtDataEuro(this.text)</xsl:eval>
  </xsl:template>
  
  <xsl:script><![CDATA[
    function totalTrafego(node)
    {
      totalTrafegado = node.selectNodes("/MainTag/EntryTag/CNPJ");
      totalTrafegado = totalTrafegado.length;
      return formatNumber(totalTrafegado, "000") + " Regs";
    }

    function totalGerN(node)
    {
      totalGeral = 0; 
      totalTrafegado = node.selectNodes("/MainTag/EntryTag/STATUS_GERAL");      
      for (v = totalTrafegado.nextNode(); v; v = totalTrafegado.nextNode())
		{
			statusGeral = v.nodeTypedValue;
	        if (statusGeral == "N")
			{
				totalGeral = totalGeral + 1;
			}
		}
      return formatNumber(totalGeral, "000") + " GerN";
    }
        
    
    function totalGerS(node)
    {
      totalGeral = 0; 
      totalTrafegado = node.selectNodes("/MainTag/EntryTag/STATUS_GERAL");      
      for (v = totalTrafegado.nextNode(); v; v = totalTrafegado.nextNode())
		{
			statusGeral = v.nodeTypedValue;
	        if (statusGeral == "S")
			{
				totalGeral = totalGeral + 1;
			}
		}
      return formatNumber(totalGeral, "000") + " GerS";
    }
        
    function totalConN(node)
    {
      totalGeral = 0; 
      totalTrafegado = node.selectNodes("/MainTag/EntryTag/STATUS_CONECT");      
      for (v = totalTrafegado.nextNode(); v; v = totalTrafegado.nextNode())
		{
			statusGeral = v.nodeTypedValue;
	        if (statusGeral == "N")
			{
				totalGeral = totalGeral + 1;
			}
		}
      return formatNumber(totalGeral, "000") + " ConN";
    }
        
    
    function totalConS(node)
    {
      totalGeral = 0; 
      totalTrafegado = node.selectNodes("/MainTag/EntryTag/STATUS_CONECT");      
      for (v = totalTrafegado.nextNode(); v; v = totalTrafegado.nextNode())
		{
			statusGeral = v.nodeTypedValue;
	        if (statusGeral == "S")
			{
				totalGeral = totalGeral + 1;
			}
		}
      return formatNumber(totalGeral, "000") + " ConS";
    }
        
    function FmtDataEuro(AAAAMMDDHHMMSS)
    {
      if (AAAAMMDDHHMMSS == "") 
          return "";
	  Ano = AAAAMMDDHHMMSS.substr(0,4);
	  Mes = AAAAMMDDHHMMSS.substr(4,2);
	  Dia = AAAAMMDDHHMMSS.substr(6,2);
	  Horas = AAAAMMDDHHMMSS.substr(8,2);
	  Minutos = AAAAMMDDHHMMSS.substr(10,2);
	  Segundos = AAAAMMDDHHMMSS.substr(12,2);
	  DataFmt = Dia + "/" + Mes + "/" + Ano;
	  HoraFmt = Horas + ":" + Minutos + ":" + Segundos;
	  DataEuro = DataFmt + "." + HoraFmt;			
	  return DataEuro;
    }

  ]]></xsl:script>
</xsl:stylesheet>
