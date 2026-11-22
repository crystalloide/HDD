package fr.orsys.hdd.tp1;

import java.io.IOException;
import java.util.Locale;
import java.util.regex.Pattern;

import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.lib.input.FileSplit;
import org.apache.hadoop.mapreduce.lib.output.MultipleOutputs;

/**
 * Collecte des informations clientèles : contrôle et normalisation de chaque
 * ligne des fichiers sources (CRM, web, magasins).
 *
 * Entrée  : id;nom;ville;ca;segment;canal;date_inscription (une ligne par client et par canal)
 * Sortie  : la même ligne, nettoyée (ville normalisée, CA à 2 décimales)
 * Rejets  : fichiers "rejets-m-*" dans le même répertoire, au format motif;fichier;ligne d'origine
 *
 * Job « map seul » : aucune agrégation, donc pas de reducer.
 */
public class CollecteMapper extends Mapper<LongWritable, Text, NullWritable, Text> {

  /** Compteurs du job, visibles dans la console et dans l'historique (JobHistory). */
  public enum Collecte { LIGNES_LUES, LIGNES_VALIDES, ENTETES, LIGNES_VIDES, REJETS }

  private static final Pattern ID = Pattern.compile("C\\d{6}");
  private static final Pattern DATE = Pattern.compile("\\d{4}-\\d{2}-\\d{2}");

  private MultipleOutputs<NullWritable, Text> sorties;
  private String fichier;
  private final Text sortie = new Text();

  @Override
  protected void setup(Context context) {
    sorties = new MultipleOutputs<>(context);
    fichier = ((FileSplit) context.getInputSplit()).getPath().getName();
  }

  @Override
  protected void map(LongWritable position, Text valeur, Context context)
      throws IOException, InterruptedException {
    context.getCounter(Collecte.LIGNES_LUES).increment(1);
    String ligne = valeur.toString();
    if (ligne.trim().isEmpty()) {
      context.getCounter(Collecte.LIGNES_VIDES).increment(1);
      return;
    }
    String[] f = ligne.split(";", -1);          // -1 : garde les champs vides en fin de ligne
    if (f.length != 7) {
      rejeter("FORMAT", ligne, context);
      return;
    }
    if (f[0].trim().equals("id")) {              // ligne d'en-tête de chaque fichier
      context.getCounter(Collecte.ENTETES).increment(1);
      return;
    }
    String id = f[0].trim();
    if (!ID.matcher(id).matches()) {
      rejeter("ID_INVALIDE", ligne, context);
      return;
    }
    String ville = Villes.normalise(f[2]);
    if (ville.isEmpty()) {
      rejeter("VILLE_ABSENTE", ligne, context);
      return;
    }
    double ca;
    try {
      ca = Double.parseDouble(f[3].trim());
    } catch (NumberFormatException e) {
      rejeter("CA_INVALIDE", ligne, context);
      return;
    }
    if (ca < 0) {
      rejeter("CA_INVALIDE", ligne, context);
      return;
    }
    String date = f[6].trim();
    if (!DATE.matcher(date).matches()) {
      rejeter("DATE_INVALIDE", ligne, context);
      return;
    }
    sortie.set(String.join(";", id, f[1].trim(), ville,
        String.format(Locale.ROOT, "%.2f", ca),
        f[4].trim().toLowerCase(Locale.ROOT), f[5].trim().toLowerCase(Locale.ROOT), date));
    context.write(NullWritable.get(), sortie);
    context.getCounter(Collecte.LIGNES_VALIDES).increment(1);
  }

  private void rejeter(String motif, String ligne, Context context)
      throws IOException, InterruptedException {
    context.getCounter(Collecte.REJETS).increment(1);
    context.getCounter("Rejets par motif", motif).increment(1);
    sorties.write(CollecteClients.SORTIE_REJETS, NullWritable.get(),
        new Text(motif + ";" + fichier + ";" + ligne), CollecteClients.SORTIE_REJETS);
  }

  @Override
  protected void cleanup(Context context) throws IOException, InterruptedException {
    sorties.close();
  }
}
