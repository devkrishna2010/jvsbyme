# J.A.R.V.I.S. V2 — Known Constraints & Engineering Roadmap

## Known Constraints & Environmental Boundaries

1. **Python 3.14 C-Extension Availability:**
   - Some legacy binary wheels (e.g. `pyaudio` or older PyTorch builds) do not distribute pre-compiled Windows binaries for Python 3.14.
   - **Mitigation:** The system uses standard library `subprocess` execution, pre-compiled standalone executables (`assets/piper/piper/piper.exe`), and pure Python modules where possible.

2. **Piper ONNX CPU Synthesis Latency:**
   - Cold synthesis of new arbitrary sentences on ONNX CPU takes ~3.0s to 3.5s per turn.
   - **Mitigation:**
     - Pre-warmed audio cache (`voice/cache/`) serves frequent acknowledgments and responses in **0.0004s** (instantaneous).
     - Non-blocking asynchronous audio playback thread allows the UI and chat logs to render immediately in 0.001s while speech synthesis runs in the background.

3. **Web Research Network Availability:**
   - When internet connectivity is offline, Wikipedia and DuckDuckGo queries cannot retrieve live remote data.
   - **Mitigation:** `skills/web_search.py` and `skills/weather.py` include automatic DNS ping checks and graceful offline fallbacks that notify the user through authentic J.A.R.V.I.S. dialogue without crashing.

4. **Multi-Monitor Cursor Avoidance Bounds:**
   - Cursor avoidance calculates repulsion vectors against the primary monitor's geometry.
   - **Mitigation:** The user can freely drag the companion to any secondary monitor, and coordinates are saved and restored cleanly.

---

## Future Roadmap (V2.1 & Beyond)

- [ ] **Dynamic Piper Memory Caching:** Maintain a warm Piper subprocess in memory via stdin/stdout pipe streaming for new arbitrary sentences.
- [ ] **Local Offline Neural Embeddings:** Add lightweight local word2vec or MiniLM sentence similarity for semantic query matching if a compatible Python 3.14 wheel becomes available.
- [ ] **Multi-Monitor Bounding Box Detection:** Automatically adapt cursor avoidance boundaries to multi-monitor virtual desktop arrangements.
- [ ] **Interactive Voice Training:** Allow the user to record custom speech samples to fine-tune Vosk acoustic models for unique regional accents.
