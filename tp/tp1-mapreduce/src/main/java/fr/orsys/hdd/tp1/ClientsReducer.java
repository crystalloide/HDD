package fr.orsys.hdd.tp1;

import java.io.IOException;

import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;

/**
 * Reduce : (ville, [1, 1, ...]) -> (ville, total)
 * Sert aussi de combiner : la somme est associative et commutative.
 */
public class ClientsReducer extends Reducer<Text, IntWritable, Text, IntWritable> {

  private final IntWritable resultat = new IntWritable();

  @Override
  protected void reduce(Text ville, Iterable<IntWritable> vals, Context ctx)
      throws IOException, InterruptedException {
    int total = 0;
    for (IntWritable v : vals) {
      total += v.get();
    }
    resultat.set(total);
    ctx.write(ville, resultat);
  }
}
