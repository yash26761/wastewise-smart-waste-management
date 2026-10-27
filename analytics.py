"""Pandas dashboard metrics and genuine local PySpark aggregations."""
import pandas as pd
from database import priority


def frame(records):
    df = pd.DataFrame(records)
    if df.empty:
        return pd.DataFrame(columns=['id','bin_code','area','location','waste_type','fill_level',
                                     'capacity_liters','status','reported_overflow','created_at',
                                     'updated_at','collected_at','priority','estimated_waste_liters'])
    df['priority'] = df.apply(lambda r: priority(r['fill_level'], r['reported_overflow'], r['status']), axis=1)
    df['estimated_waste_liters'] = (df['fill_level'] * df['capacity_liters'] / 100).round(1)
    return df


def summary(df):
    if df.empty:
        return dict(total=0, full=0, pending=0, collected_liters=0.0)
    return dict(total=len(df),
                full=int(((df.fill_level >= 90) | (df.reported_overflow == 1)).sum()),
                pending=int((df.status != 'Collected').sum()),
                collected_liters=float(df.loc[df.status == 'Collected', 'estimated_waste_liters'].sum()))


def spark_analytics(df):
    """Actual PySpark DataFrame groupBy/aggregation, executed only when requested."""
    import os
    import sys
    os.environ['PYSPARK_PYTHON'] = sys.executable
    os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable
    from pyspark.sql import SparkSession, functions as F, types as T
    spark = (SparkSession.builder.master('local[1]').appName('WasteWiseAnalytics')
             .config('spark.pyspark.python', sys.executable)
             .config('spark.pyspark.driver.python', sys.executable)
             .config('spark.driver.bindAddress', '127.0.0.1')
             .config('spark.driver.host', '127.0.0.1')
             .config('spark.ui.enabled', 'false')
             .config('spark.driver.memory', '1g')
             .config('spark.sql.shuffle.partitions', '1')
             .getOrCreate())
    spark.sparkContext.setLogLevel('ERROR')
    schema = T.StructType([
        T.StructField('area', T.StringType(), False),
        T.StructField('waste_type', T.StringType(), False),
        T.StructField('status', T.StringType(), False),
        T.StructField('priority', T.StringType(), False),
        T.StructField('estimated_waste_liters', T.DoubleType(), False),
    ])
    rows = [(str(r.area), str(r.waste_type), str(r.status), str(r.priority),
             float(r.estimated_waste_liters)) for r in df.itertuples(index=False)]
    try:
        sdf = spark.createDataFrame(rows, schema)
        by_area = (sdf.groupBy('area').agg(
            F.count('*').alias('bins'),
            F.round(F.sum('estimated_waste_liters'), 1).alias('estimated_liters'),
            F.sum(F.when(F.col('priority') == 'High', 1).otherwise(0)).alias('high_priority'))
            .orderBy(F.desc('estimated_liters')))
        by_type = (sdf.groupBy('waste_type').agg(
            F.count('*').alias('bins'),
            F.round(F.sum('estimated_waste_liters'), 1).alias('estimated_liters'))
            .orderBy(F.desc('estimated_liters')))
        by_status = (sdf.groupBy('status').count().orderBy('status'))
        return {'area': [r.asDict() for r in by_area.collect()],
                'type': [r.asDict() for r in by_type.collect()],
                'status': [r.asDict() for r in by_status.collect()],
                'processed': sdf.count()}
    finally:
        # Each analysis ends its session; suitable for small college demo datasets.
        spark.stop()
