const { createApp, nextTick } = Vue;

createApp({
  data() {
    return {
      query: '',
      messages: [],
      sources: [],
      status: '',
      loading: false
    };
  },
  methods: {
    async send() {
      const text = this.query.trim();
      if (!text || this.loading) return;

      this.loading = true;
      this.status = 'Thinking...';
      this.sources = [];

      this.messages.push({ role: 'user', content: text });
      this.query = '';
      await nextTick();
      this.scrollToBottom();

      try {
        const resp = await fetch(`${API_ENDPOINT}/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: text,
            history: this.messages.slice(-HISTORY_LIMIT)
          })
        });

        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || 'Request failed');

        this.messages.push({
          role: 'assistant',
          content: data.answer || 'No answer.'
        });

        if (Array.isArray(data.sources)) {
          this.sources = data.sources;
        }

        if (!this.sources.length) {
          this.status = `No sources found (top_k=${TOP_K}, threshold=${SIMILARITY_THRESHOLD}). Try a broader query.`;
        } else {
          this.status = 'Done';
        }
        await nextTick();
        this.scrollToBottom();
      } catch (err) {
        this.status = `Error: ${err.message}`;
      } finally {
        this.loading = false;
      }
    },
    resetChat() {
      this.messages = [];
      this.sources = [];
      this.status = '';
      this.query = '';
    },
    scrollToBottom() {
      const el = document.querySelector('.chat');
      if (el) el.scrollTop = el.scrollHeight;
    }
  }
}).mount('#app');
