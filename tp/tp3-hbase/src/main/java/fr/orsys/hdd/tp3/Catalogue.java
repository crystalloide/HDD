package fr.orsys.hdd.tp3;

import java.time.LocalDate;
import java.time.ZoneOffset;

import org.apache.hadoop.hbase.TableName;
import org.apache.hadoop.hbase.util.Bytes;

/** Constantes partagées par les programmes du TP : table, familles, colonnes. */
final class Catalogue {

  static final TableName TABLE = TableName.valueOf("catalogue");
  static final byte[] INFO = Bytes.toBytes("info");
  static final byte[] STOCK = Bytes.toBytes("stock");
  static final byte[] PRIX = Bytes.toBytes("prix");

  private Catalogue() { }

  /** Date "aaaa-mm-jj" -> horodatage HBase (millisecondes, minuit UTC). */
  static long horodatage(String date) {
    return LocalDate.parse(date).atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli();
  }
}
