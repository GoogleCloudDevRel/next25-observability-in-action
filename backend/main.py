import os
import random
import datetime
import requests
import json


from quart import Quart, request, jsonify
from google.cloud import firestore
import google.auth.transport.requests
import google.oauth2.id_token

from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
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

app = Quart(__name__)
app.asgi_app = OpenTelemetryMiddleware(app.asgi_app)

PROJECT=os.getenv("GOOGLE_CLOUD_PROJECT")
GEMMA_ENDPOINT=os.getenv("GEMMA_ENDPOINT")
LLM_BACKENDS = {
  "gemini-flash": models.getGemini(PROJECT, model="gemini-2.0-flash"),
  "gemini-flash-lite": models.getGemini(PROJECT, model="gemini-2.0-flash-lite")
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

@app.route("/prompt", methods=['POST'])
async def call_llm():
  prompt = request.args.get("prompt")
  session_id = request.args.get("sid")

  # print (prompt)
  # print (session_id)
  
  for llm_key in LLM_BACKENDS:
     await call_gemini(prompt, llm_key, session_id)
  await call_gemma(prompt, session_id)
  return jsonify({"content": f"prompts processed for {session_id}"})

async def call_gemini(prompt,model,sid):
  llm = LLM_BACKENDS[model]
  resp = ""
  with tracer.start_as_current_span(f"calling {model}") as span:
    span.set_attribute(key="model", value=model)
    starttime = datetime.datetime.now()
    resp = llm.invoke(prompt)
    stoptime = datetime.datetime.now()
    llmlatency = (stoptime - starttime) / datetime.timedelta(milliseconds=1)
    logger.info("LLM called", model=model, latency=llmlatency, prompt=prompt, session_id=sid)
    llm_histogram.record(llmlatency, attributes={'model': model})
    llm_count.add(1, attributes={'model': model})
  return resp


async def call_gemma(prompt,sid):
  url = f'{GEMMA_ENDPOINT}/api/generate'
  data = {
      "model": "gemma3:1b",
      "prompt": prompt
  }
  model = "Gemma"
  auth_req = google.auth.transport.requests.Request()
  id_token = google.oauth2.id_token.fetch_id_token(auth_req, url)


  headers = {
    'Content-Type': 'application/json',
    'Authorization': f"Bearer {id_token}"
  }
  response = ""
  with tracer.start_as_current_span(f"calling {model}") as span:
    span.set_attribute(key="model", value=model)
    starttime = datetime.datetime.now()
    try:
      response = requests.post(url, data=json.dumps(data), headers=headers) # Use json.dumps to convert the dictionary to a JSON string
    except: 
      pass
    #print (response.text)
    stoptime = datetime.datetime.now()
    llmlatency = (stoptime - starttime) / datetime.timedelta(milliseconds=1)
    logger.info("LLM called", model=model, latency=llmlatency, prompt=prompt, session_id=sid)
    llm_histogram.record(llmlatency, attributes={'model': model})
    llm_count.add(1, attributes={'model': model})
  return response


@app.route("/llmz")
def debug_list_backends():
  return jsonify(list(LLM_BACKENDS.keys()))


if __name__ == "__main__":
  app.run()
