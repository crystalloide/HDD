package fr.orsys.hdd.tp1;

import java.io.IOException;

import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;

/**
 * Map : (position, "id;nom;ville;...") -> (ville, 1)
 * Code du support de cours, plus une pause optionnelle (hdd.map.pause.ms)
 * utilisée au TP YARN pour observer les conteneurs pendant l'exécution.
 */
public class ClientsMapper extends Mapper<LongWritable, Text, Text, IntWritable> {

  private static final IntWritable UN = new IntWritable(1);
  private final Text ville = new Text();

  @Override
  protected void setup(Context ctx) throws InterruptedException {
    long pause = ctx.getConfiguration().getLong("hdd.map.pause.ms", 0L);
    if (pause > 0) {
      Thread.sleep(pause);
    }
  }

  @Override
  protected void map(LongWritable off, Text ligne, Context ctx)
      throws IOException, InterruptedException {
    String[] f = ligne.toString().split(";");   // id;nom;ville;...
    if (f.length >= 3) {
      ville.set(f[2]);
      ctx.write(ville, UN);
    }
  }
}
