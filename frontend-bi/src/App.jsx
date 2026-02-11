import React, { useState, useCallback, useRef, useEffect } from 'react';
import { GraphicWalker } from '@kanaries/graphic-walker';

const App = () => {
  const [messages, setMessages] = useState([]);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  // Estado para el panel derecho (GraphicWalker)
  const [gwData, setGwData] = useState([]);
  const [gwFields, setGwFields] = useState([]);
  const [gwChart, setGwChart] = useState(undefined);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Genera campos dinámicos a partir de los datos reales del backend
  const generateFields = (data) => {
    if (!data || data.length === 0) return [];
    const sample = data[0];
    return Object.keys(sample).map(key => {
      const value = sample[key];
      let semanticType = 'nominal';
      let analyticType = 'dimension';

      if (typeof value === 'number') {
        semanticType = 'quantitative';
        analyticType = 'measure';
      } else if (typeof value === 'string' && !isNaN(Date.parse(value)) && value.includes('-')) {
        semanticType = 'temporal';
        analyticType = 'dimension';
      }

      return {
        fid: key,
        name: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' '),
        semanticType,
        analyticType,
      };
    });
  };

  const handleAskBackend = useCallback(async () => {
    if (!prompt.trim()) return;
    const userMsg = prompt.trim();
    setPrompt("");
    setLoading(true);

    // Agregar mensaje del usuario al chat
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);

    try {
      const response = await fetch('http://127.0.0.1:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userMsg })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || response.statusText);
      }

      const data = await response.json();
      console.log("Backend Response:", data);

      if (data.status === 'success' && data.data && data.data.length > 0) {
        const fields = generateFields(data.data);
        console.log("Dynamic Fields:", fields);

        // Crear configuración de gráfico automático
        const dims = fields.filter(f => f.analyticType === 'dimension');
        const meas = fields.filter(f => f.analyticType === 'measure');
        const dim = dims[0];
        const measure = meas[0];

        if (dim && measure) {
          const autoChart = [{
            visId: 'auto_' + Date.now(),
            name: userMsg,
            encodings: {
              dimensions: dims.map(d => ({ fid: d.fid, name: d.name, semanticType: d.semanticType, analyticType: 'dimension' })),
              measures: meas.map(m => ({ fid: m.fid, name: m.name, semanticType: m.semanticType, analyticType: 'measure', aggName: 'sum' })),
              rows: [{ fid: measure.fid, name: measure.name, semanticType: measure.semanticType, analyticType: 'measure', aggName: 'sum' }],
              columns: [{ fid: dim.fid, name: dim.name, semanticType: dim.semanticType, analyticType: 'dimension' }],
              color: [],
              opacity: [],
              size: [],
              shape: [],
              theta: [],
              radius: [],
              longitude: [],
              latitude: [],
              geoId: [],
              details: [],
              filters: [],
              text: [],
            },
            config: {
              defaultAggregated: true,
              geoms: [data.metadata.suggested_chart === 'line' ? 'line' : data.metadata.suggested_chart === 'pie' ? 'arc' : 'bar'],
              coordSystem: 'generic',
              limit: -1,
            },
            layout: {
              showActions: false,
              showTableSummary: false,
              interactiveScale: false,
              stack: 'stack',
              size: { mode: 'auto' },
            },
          }];
          setGwChart(autoChart);
          console.log("Auto Chart Config:", autoChart);
        }

        // Actualizar el panel derecho con los nuevos datos
        setGwData(data.data);
        setGwFields(fields);

        // Agregar confirmación al chat
        setMessages(prev => [...prev, {
          role: 'assistant',
          text: `✅ Consulta ejecutada. Se encontraron ${data.data.length} resultados con los campos: ${fields.map(f => f.name).join(', ')}. Los datos están cargados en el panel de visualización. Puedes cambiar el tipo de gráfico, arrastrar campos y aplicar filtros.`
        }]);
      } else if (data.data && data.data.length > 0 && data.data[0].error) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          text: `❌ Error en la consulta SQL: ${data.data[0].error}`
        }]);
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          text: '⚠️ No se encontraron datos para tu consulta. Intenta con otra pregunta.'
        }]);
      }

    } catch (e) {
      console.error("Error:", e);
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: `❌ Error: ${e.message}`
      }]);
    } finally {
      setLoading(false);
    }
  }, [prompt]);

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', fontFamily: "'Segoe UI', 'Inter', sans-serif", backgroundColor: '#0d1117', color: '#e6edf3' }}>
      
      {/* ===== PANEL IZQUIERDO: CHAT ===== */}
      <div style={{ 
        width: '360px', minWidth: '360px', 
        display: 'flex', flexDirection: 'column',
        borderRight: '1px solid #21262d', backgroundColor: '#161b22'
      }}>
        {/* Chat Header */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #21262d', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '1.4rem' }}>🤖</span>
          <div>
            <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>Asistente BI</h2>
            <small style={{ color: '#8b949e', fontSize: '0.75rem' }}>Gemini AI · PostgreSQL</small>
          </div>
        </div>

        {/* Chat Messages */}
        <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', color: '#8b949e', marginTop: '40px' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>💬</div>
              <p style={{ fontSize: '0.85rem', lineHeight: 1.6 }}>
                Escribe una pregunta para consultar tu base de datos.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '16px' }}>
                {[
                  'Rendimiento de los vendedores',
                  'Ventas por categoría',
                  'Ventas por región'
                ].map(q => (
                  <button key={q} onClick={() => setPrompt(q)} style={{
                    padding: '8px 14px', backgroundColor: '#21262d', border: '1px solid #30363d',
                    borderRadius: '8px', color: '#8b949e', cursor: 'pointer', fontSize: '0.82rem',
                    textAlign: 'left', transition: 'all 0.2s'
                  }}>💡 {q}</button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} style={{
              marginBottom: '12px',
              display: 'flex', flexDirection: 'column',
              alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start'
            }}>
              <div style={{
                maxWidth: '90%', padding: '10px 14px', borderRadius: '12px',
                backgroundColor: msg.role === 'user' ? '#238636' : '#21262d',
                fontSize: '0.88rem', lineHeight: 1.5
              }}>
                {msg.text}
              </div>
              <small style={{ color: '#484f58', marginTop: '3px', fontSize: '0.7rem' }}>
                {msg.role === 'user' ? 'Tú' : 'IA'}
              </small>
            </div>
          ))}

          {loading && (
            <div style={{ color: '#8b949e', fontSize: '0.85rem', padding: '8px' }}>
              <span style={{ animation: 'pulse 1.5s infinite' }}>⏳</span> Analizando...
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Chat Input */}
        <div style={{ padding: '12px 16px', borderTop: '1px solid #21262d' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Escribe tu consulta..."
              style={{
                flex: 1, padding: '10px 14px', borderRadius: '8px', border: '1px solid #30363d',
                backgroundColor: '#0d1117', color: '#e6edf3', fontSize: '0.9rem', outline: 'none'
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleAskBackend();
                }
              }}
            />
            <button
              onClick={handleAskBackend}
              disabled={loading || !prompt.trim()}
              style={{
                padding: '10px 16px', borderRadius: '8px', border: 'none',
                backgroundColor: loading || !prompt.trim() ? '#21262d' : '#238636',
                color: 'white', fontWeight: 600, cursor: loading ? 'wait' : 'pointer', fontSize: '0.9rem'
              }}
            >
              {loading ? '⏳' : '➤'}
            </button>
          </div>
        </div>
      </div>

      {/* ===== PANEL DERECHO: GRAPHIC WALKER ===== */}
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {gwData.length > 0 ? (
          <div style={{ flex: 1, overflow: 'auto' }}>
            <GraphicWalker
              key={JSON.stringify(gwFields.map(f => f.fid))}
              dataSource={gwData}
              rawFields={gwFields}
              chart={gwChart}
              appearance="dark"
              i18nLang="es-ES"
            />
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100%', color: '#484f58' }}>
            <div style={{ fontSize: '4rem', marginBottom: '16px' }}>📊</div>
            <h3 style={{ fontWeight: 500, color: '#8b949e' }}>Panel de Visualización Interactiva</h3>
            <p style={{ maxWidth: '400px', textAlign: 'center', lineHeight: 1.6, fontSize: '0.9rem' }}>
              Haz una pregunta en el chat para cargar datos aquí. Podrás cambiar tipos de gráfico, arrastrar campos y aplicar filtros — estilo Grafana/Tableau.
            </p>
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        input::placeholder { color: #484f58; }
        *::-webkit-scrollbar { width: 6px; }
        *::-webkit-scrollbar-track { background: transparent; }
        *::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
      `}</style>
    </div>
  );
};

export default App;