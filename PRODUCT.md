# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Python stdlib only (`http.server`, no framework), one HTML page with self-hosted fonts. It has to run from the project venv on both machines, Linux and Windows, with nothing to install.

## Users

The two people running the acoustic-modem bench, one at each machine, watching a negotiated link (`enlace.py` through `saudacao.py`) come up by sound alone, and starting sessions from that same machine.

## Product Purpose

An acoustic modem that negotiates its own link over the air: hail, control frames, a sounding per direction, a contract per direction decided by the receiver, then stop-and-wait data. The screens that matter show whether that handshake is progressing, what each side heard, and what was delivered.

## Operating Context

Each machine runs its own session (`saudacao.py`, one `chamador`, one `ouvinte`) and its own `painel` server on 127.0.0.1:7110, which publishes state, the session diary, and writes the microphone input continuously to disk. A session lasts minutes. The serial cable or SSH tunnel may observe, never negotiate.

## Capabilities and Constraints

- Local only: each screen is opened on its own machine; no remote view.
- Must not modify `enlace.py`, `saudacao.py` or `painel.py`; reads only what the panel publishes and what it writes to disk.
- Audio in the views is the raw microphone, own transmission included.
- Received bytes are only available when the session writes `--receber-em`, at completion.

## Brand Commitments

Visual world pinned by the user: a 1940s radio set, rusted pastel tones, the radio's tuning dial; no explicit war references. Everything on screen must carry a purpose.

## Product Principles

- Measured, not assumed: every readout comes from the panel, the diary or the recorded audio.
- The frequency axis is the shared ruler: contracts, shadows, margins and the live spectrum all sit on the same 162.5 Hz grid.
- Never hide the failure mode: unreadable frames, lag behind real time and warnings are shown as loudly as success.
