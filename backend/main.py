import os
import random
import datetime

from flask import Flask, request, jsonify
from google.cloud import firestore

from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

from gcplogger import getJSONLogger
import models

logger = getJSONLogger()

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

PROJECT=os.getenv("GOOGLE_CLOUD_PROJECT")
LLM_BACKENDS = {
  "gemini-flash": models.getGemini(PROJECT, model="gemini-2.0-flash"),
  "gemini-flash-lite": models.getGemini(PROJECT, model="gemini-2.0-flash-lite"),
}

fclient = firestore.Client(
  project=PROJECT,
  database="o11ydemo",
)


def setup_otel(project):
  tprovider = TracerProvider(sampler=ALWAYS_ON)
  trace.set_tracer_provider(tprovider)
  trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(insecure=True))
  )
  mreader = PeriodicExportingMetricReader(OTLPMetricExporter())
  mprovider = MeterProvider(metric_readers=[mreader])
  metrics.set_meter_provider(mprovider)

setup_otel(os.getenv("GOOGLE_CLOUD_PROJECT"))
tracer = trace.get_tracer(__name__)

#define metrics for use below.
meter = metrics.get_meter("quizdemo")
q_counter = meter.create_counter("questions_asked")
answer_counter = meter.create_counter("questions_answered")
llm_count = meter.create_counter("llm_requests")
llm_histogram = meter.create_histogram(
  name="llm_latency",
  unit="ms",
  description="latency of proxied llm requests, in milliseconds"
)
question_latency = meter.create_histogram(
  name="questions_latency",
  unit="ms",
  description="latency of quiz question requests, in milliseconds"
)
 
@app.route("/")
def health():
  return "ok", 200

@app.route("/question")
def random_q():
  starttime = datetime.datetime.now()
  c = fclient.collection('questions')
  doclist = []
  for d in c.list_documents():
    doclist.append(d)
    
  i = random.randint(0, len(doclist)-1)
  r = doclist[i]
  stoptime = datetime.datetime.now()
  latency = (stoptime - starttime) / datetime.timedelta(milliseconds=1)
  question_latency.record(latency, attributes={'qid': r.id})
  logger.info("asking question", qid=r.id, latency=latency)
  q_counter.add(1)
  return docref_for_output(r)

@app.route("/question/<qid>", methods=['GET'])
def get_question(qid):
  #debug shortcut. if we have a query string, call the post version.
  if request.args.get("answer", None):
    return score_question(qid)
  dr = fclient.collection('questions').document(qid)
  logger.info("asking question", qid=dr.id)
  q_counter.add(1)
  return docref_for_output(dr)

# format a docref for output by flask.
def docref_for_output(docref):
  rv = docref.get().to_dict()
  rv['id'] = docref.id
  return jsonify(rv)

@app.route("/question/<qid>", methods=['POST'])
def score_question(qid):
  got = request.args.get("answer", None)
  dr = fclient.collection('questions').document(qid)
  want = dr.get().get("answer")
  logger.info("scoring question", qid=dr.id, correct=(got == want))
  answer_counter.add(1, attributes={'correct': (got == want), 'qid': dr.id})
  return jsonify({"correct": got == want,
                  "right_answer": want })

@app.route("/prompt/<model>")
def call_llm(model):
  prompt = request.args.get("prompt")
  if model not in LLM_BACKENDS:
    return f"unknown model requested: {model}", 400
  llm = LLM_BACKENDS[model]
  with tracer.start_as_current_span("calling llm") as span:
    span.set_attribute(key="model", value=model)
    starttime = datetime.datetime.now()
    resp = llm.invoke(prompt)
    stoptime = datetime.datetime.now()
    llmlatency = (stoptime - starttime) / datetime.timedelta(milliseconds=1)
    logger.info("LLM called", model=model, latency=llmlatency, prompt=prompt)
    llm_histogram.record(llmlatency, attributes={'model': model})
    llm_count.add(1, attributes={'model': model})
  return jsonify({"content": resp.content})

@app.route("/llmz")
def debug_list_backends():
  return jsonify(list(LLM_BACKENDS.keys()))


if __name__ == "__main__":
  app.run()
