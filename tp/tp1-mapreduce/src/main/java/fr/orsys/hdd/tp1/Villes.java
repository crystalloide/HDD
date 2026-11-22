package fr.orsys.hdd.tp1;

import java.text.Normalizer;
import java.util.Locale;

/**
 * Règle de normalisation des villes, commune à tout le lab
 * (mapper de collecte, UDF Pig NormaliseVille, version PySpark) :
 * espaces superflus retirés, accents retirés, majuscules.
 * "  saint-étienne " -> "SAINT-ETIENNE"
 */
public final class Villes {

  private Villes() { }

  public static String normalise(String brute) {
    if (brute == null) {
      return "";
    }
    String sansAccents = Normalizer.normalize(brute, Normalizer.Form.NFD)
        .replaceAll("\\p{M}+", "");
    return sansAccents.trim().replaceAll("\\s+", " ").toUpperCase(Locale.ROOT);
  }
}
