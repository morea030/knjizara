import datetime
from app import models
import app
import whoosh
import flask_whooshalchemy

# from app.rebuild_search_indeces import rebuild_index

program_start = datetime.datetime.utcnow()

def log(message):
    logtime = datetime.datetime.utcnow()
    logdiff = logtime - program_start
    print("{0} (+{1:.3f}): {2}".format(logtime.strftime("%Y-%m-%d %H:%M:%S"),
                                    logdiff.total_seconds(),
                                    message))

def rebuild_index(model):
    """Rebuild whoosh search index of  Flask-SQLAlchemy model"""
    log("Rebuilding {0} index...".format(model.__name__))
    primary_field = model.pure_whoosh.primary_key_name
    searchables = model.__searchable__
    index_writer = flask_whooshalchemy.whoosh_index(app, model)

    # Fetch all data
    entries = model.query.all()

    entry_count = 0
    with index_writer.writer() as writer:
        for entry in entries:
            index_attrs = {}
            for field in searchables:
                index_attrs[field] = unicode(getattr(entry, field))

            index_attrs[primary_field] = unicode(getattr(entry, primary_field))
            writer.update_document(**index_attrs)
            entry_count += 1

    log("Rebuilt {0} {1} search index entries.".format(str(entry_count), model.__name__))