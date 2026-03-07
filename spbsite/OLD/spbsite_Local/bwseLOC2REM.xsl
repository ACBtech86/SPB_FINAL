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
              <P><xsl:eval>totalREQ(this)</xsl:eval></P>
              <P><xsl:eval>totalRSP(this)</xsl:eval></P>
              <P><B><xsl:eval>totalTrafego(this)</xsl:eval></B></P>
              <P>                                               </P>
              <P>Clique no cabecalho da coluna para classificar.</P>
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
        <TD width="200"><DIV class="fntCabecTab" onClick="Classifica('DB_DATETIME')">DB_DATETIME</DIV></TD>
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('STATUS_MSG')">STATUS_MSG</DIV></TD>
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('FLAG_PROC')">FLAG_PROC</DIV></TD>
        <TD width="220"><DIV class="fntCabecTab" onClick="Classifica('MQ_QN_DESTINO')">MQ_QN_DESTINO</DIV></TD>
        <TD width="200"><DIV class="fntCabecTab" onClick="Classifica('MQ_DATETIME_PUT')">MQ_DATETIME_PUT</DIV></TD>
		<TD width="200"><DIV class="fntCabecTab" onClick="Classifica('MQ_DATETIME_COA')">MQ_DATETIME_COA</DIV></TD>
		<TD width="200"><DIV class="fntCabecTab" onClick="Classifica('MQ_DATETIME_COD')">MQ_DATETIME_COD</DIV></TD>
		<TD width="200"><DIV class="fntCabecTab" onClick="Classifica('MQ_DATETIME_REP')">MQ_DATETIME_REP</DIV></TD>
        <TD width="300"><DIV class="fntCabecTab" onClick="Classifica('NU_OPE')">NU_OPE</DIV></TD>
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('COD_MSG')">COD_MSG</DIV></TD>
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('MSG')">MSG</DIV></TD>
      </TCabecalho>
      
      <xsl:for-each select="EntryTag" order-by="DB_DATETIME">
        <TR>
 		  <xsl:choose>
		    <xsl:when test="STATUS_MSG[. $eq$ 'P']">
                <xsl:attribute name="class">Cor_Aviso</xsl:attribute>
		    </xsl:when>
		    <xsl:when test="STATUS_MSG[. $eq$ 'R']">
                <xsl:attribute name="class">Cor_Erro</xsl:attribute>
		    </xsl:when>
		    <xsl:when test="STATUS_MSG[. $eq$ 'E']">
                <xsl:attribute name="class">Cor_Erro</xsl:attribute>
		    </xsl:when>
		    <xsl:otherwise>
                <xsl:attribute name="class">Cor_Normal</xsl:attribute>
	        </xsl:otherwise>

		  </xsl:choose>

          <TD><DIV class="fntLinhaTab"><xsl:apply-templates select="DB_DATETIME"/></DIV></TD>  
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="STATUS_MSG"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="FLAG_PROC"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="MQ_QN_DESTINO"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:apply-templates select="MQ_DATETIME_PUT"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:apply-templates select="MQ_DATETIME_COA"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:apply-templates select="MQ_DATETIME_COD"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:apply-templates select="MQ_DATETIME_REP"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="NU_OPE"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="COD_MSG"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><![CDATA[<xsl:value-of select="MSG"/>]]></DIV></TD>
        </TR>
      </xsl:for-each>
    </TABLE>
  </xsl:template>


  <xsl:template match="DB_DATETIME | MQ_DATETIME | MQ_DATETIME_PUT | MQ_DATETIME_COA | MQ_DATETIME_COD | MQ_DATETIME_REP">
    <xsl:eval>FmtDataEuro(this.text)</xsl:eval>
  </xsl:template>
  
  <xsl:script><![CDATA[
    function totalTrafego(node)
    {
      totalTrafegado = node.selectNodes("/MainTag/EntryTag/DB_DATETIME");
      totalTrafegado = totalTrafegado.length;
      return formatNumber(totalTrafegado, "000") + " Msgs";
    }

    function totalREQ(node)
    {
      totalREQ = 0; 
      totalTrafegado = node.selectNodes("/MainTag/EntryTag/MQ_QN_DESTINO");      
      for (v = totalTrafegado.nextNode(); v; v = totalTrafegado.nextNode())
		{
			fila = v.nodeTypedValue;
		    tipoFila = fila.substr(3,3);
	        if (tipoFila == "REQ")
			{
				totalREQ = totalREQ + 1;
			}
		}
      return formatNumber(totalREQ, "000") + " REQs";
    }
        
    
    function totalRSP(node)
    {
      totalRSP = 0; 
      totalTrafegado = node.selectNodes("/MainTag/EntryTag/MQ_QN_DESTINO");
      for (v = totalTrafegado.nextNode(); v; v = totalTrafegado.nextNode())
		{
			fila = v.nodeTypedValue;
		    tipoFila = fila.substr(3,3);
	        if (tipoFila == "RSP")
			{
				totalRSP = totalRSP + 1;
			}
		}
      return formatNumber(totalRSP, "000") + " RSPs";
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
