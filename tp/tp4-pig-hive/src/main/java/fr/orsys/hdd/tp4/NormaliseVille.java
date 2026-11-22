package fr.orsys.hdd.tp4;

import java.io.IOException;
import java.text.Normalizer;
import java.util.Locale;

import org.apache.pig.EvalFunc;
import org.apache.pig.data.Tuple;

/**
 * UDF Pig (Pig appelle Java) : normalise un nom de ville.
 * "  saint-étienne " -> "SAINT-ETIENNE" ; chaîne vide ou absente -> null.
 *
 * Utilisation dans un script :
 *   REGISTER '/tmp/hdd/tp4/udfs.jar';
 *   DEFINE NormaliseVille fr.orsys.hdd.tp4.NormaliseVille();
 *   b = FOREACH a GENERATE NormaliseVille(ville);
 *
 * Même règle que le mapper de collecte du TP1 et que la version PySpark du TP5.
 */
public class NormaliseVille extends EvalFunc<String> {

  @Override
  public String exec(Tuple in) throws IOException {
    if (in == null || in.size() == 0 || in.get(0) == null) {
      return null;
    }
    String v = Normalizer.normalize(in.get(0).toString(), Normalizer.Form.NFD)
        .replaceAll("\\p{M}+", "")
        .trim()
        .replaceAll("\\s+", " ")
        .toUpperCase(Locale.ROOT);
    return v.isEmpty() ? null : v;
  }
}
