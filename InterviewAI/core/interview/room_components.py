"""Module 5 — Interview Room Components.

HTML/JS templates for the live interview interface with
mic/camera controls, question display, and recording indicators.
"""

DEVICE_SETUP_HTML = """
<div id="interview-room" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
    <div id="setup-panel" style="
        background: linear-gradient(135deg, #f7fafc, #edf2f7);
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    ">
        <h3 style="color: #2d3748; margin: 0 0 20px 0; font-size: 1.2rem;">
            &#127908; Device Setup &mdash; Check before starting
        </h3>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <!-- Microphone -->
            <div style="background: white; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                    <span style="font-size: 1.5rem;">&#127908;</span>
                    <span style="font-weight: 600; color: #2d3748;">Microphone</span>
                </div>
                <div id="mic-status" style="
                    padding: 8px 16px; border-radius: 20px; display: inline-block;
                    font-size: 0.85rem; font-weight: 500;
                    background: #fed7d7; color: #c53030;
                ">&#9679; Not Connected</div>
                <br><br>
                <button onclick="testMicrophone()" style="
                    background: linear-gradient(135deg, #2c5282, #4299e1);
                    color: white; border: none; padding: 10px 20px;
                    border-radius: 8px; cursor: pointer; font-weight: 500;
                ">Test Microphone</button>
                <div id="mic-level" style="
                    margin-top: 12px; height: 6px; background: #e2e8f0; 
                    border-radius: 3px; overflow: hidden;
                ">
                    <div id="mic-level-bar" style="height: 100%; width: 0%; background: #48BB78; transition: width 0.1s;"></div>
                </div>
            </div>
            
            <!-- Camera -->
            <div style="background: white; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                    <span style="font-size: 1.5rem;">&#128247;</span>
                    <span style="font-weight: 600; color: #2d3748;">Camera</span>
                </div>
                <div id="cam-status" style="
                    padding: 8px 16px; border-radius: 20px; display: inline-block;
                    font-size: 0.85rem; font-weight: 500;
                    background: #fed7d7; color: #c53030;
                ">&#9679; Not Connected</div>
                <br><br>
                <button onclick="testCamera()" style="
                    background: linear-gradient(135deg, #2c5282, #4299e1);
                    color: white; border: none; padding: 10px 20px;
                    border-radius: 8px; cursor: pointer; font-weight: 500;
                ">Test Camera</button>
                <div style="margin-top: 12px;">
                    <video id="camera-preview" autoplay muted playsinline style="
                        width: 100%; max-height: 150px; border-radius: 8px;
                        background: #1a202c; display: none;
                    "></video>
                </div>
            </div>
        </div>
        
        <!-- Ready Status -->
        <div id="ready-status" style="
            margin-top: 20px; padding: 12px 20px;
            border-radius: 10px; text-align: center;
            background: #fffff0; border: 1px solid #fefcbf;
            color: #975a16; font-weight: 500;
        ">
            &#9888; Please test your microphone and camera before starting
        </div>
    </div>
</div>

<script>
let micStream = null;
let camStream = null;
let audioContext = null;
let analyser = null;
let micReady = false;
let camReady = false;

async function testMicrophone() {
    try {
        micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        document.getElementById('mic-status').innerHTML = '&#9679; Connected';
        document.getElementById('mic-status').style.background = '#c6f6d5';
        document.getElementById('mic-status').style.color = '#276749';
        micReady = true;
        
        audioContext = new AudioContext();
        const source = audioContext.createMediaStreamSource(micStream);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        function updateLevel() {
            analyser.getByteFrequencyData(dataArray);
            const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
            const pct = Math.min(100, (avg / 128) * 100);
            document.getElementById('mic-level-bar').style.width = pct + '%';
            if (micReady) requestAnimationFrame(updateLevel);
        }
        updateLevel();
        checkReady();
    } catch (err) {
        document.getElementById('mic-status').innerHTML = '&#9679; Denied: ' + err.message;
    }
}

async function testCamera() {
    try {
        camStream = await navigator.mediaDevices.getUserMedia({ video: true });
        document.getElementById('cam-status').innerHTML = '&#9679; Connected';
        document.getElementById('cam-status').style.background = '#c6f6d5';
        document.getElementById('cam-status').style.color = '#276749';
        camReady = true;
        
        const video = document.getElementById('camera-preview');
        video.srcObject = camStream;
        video.style.display = 'block';
        checkReady();
    } catch (err) {
        document.getElementById('cam-status').innerHTML = '&#9679; Denied: ' + err.message;
    }
}

function checkReady() {
    const el = document.getElementById('ready-status');
    if (micReady && camReady) {
        el.innerHTML = '&#10004; All devices ready &mdash; You can start the interview';
        el.style.background = '#f0fff4';
        el.style.border = '1px solid #9ae6b4';
        el.style.color = '#276749';
    } else if (micReady || camReady) {
        const missing = micReady ? 'Camera' : 'Microphone';
        el.innerHTML = '&#9888; ' + missing + ' not tested yet';
    }
}
</script>
"""


def get_interview_question_html(question: str, q_number: int, total: int,
                                 q_type: str, skill: str = "") -> str:
    """Generate the live interview question display HTML."""
    type_styles = {
        "opening": ("#ebf8ff", "#2c5282", "OPENING"),
        "technical": ("#fff5f5", "#c53030", "TECHNICAL"),
        "behavioural": ("#f0fff4", "#276749", "BEHAVIOURAL"),
        "closing": ("#faf5ff", "#553c9a", "CLOSING"),
    }
    bg, color, label = type_styles.get(q_type, ("#f7fafc", "#4a5568", q_type.upper()))

    return f"""
    <div style="
        background: linear-gradient(135deg, #1a202c, #2d3748);
        border-radius: 16px; padding: 40px; color: white;
        text-align: center; min-height: 300px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
    ">
        <div style="font-size: 2.5rem; margin-bottom: 16px;">&#129504;</div>
        <div style="font-size: 0.8rem; color: #a0aec0; margin-bottom: 8px; letter-spacing: 1px;">
            QUESTION {q_number} OF {total}
        </div>
        <div style="
            font-size: 1.25rem; font-weight: 500; line-height: 1.7;
            max-width: 600px; color: #e2e8f0; margin: 10px 0 20px 0;
        ">&ldquo;{question}&rdquo;</div>
        <div style="display: flex; gap: 8px; align-items: center;">
            <span style="
                padding: 6px 14px; border-radius: 20px;
                font-size: 0.75rem; font-weight: 600;
                background: {bg}; color: {color};
            ">{label}</span>
            {"<span style='padding: 6px 14px; border-radius: 20px; font-size: 0.75rem; background: #2d3748; color: #a0aec0;'>" + skill + "</span>" if skill else ""}
        </div>
    </div>
    """


def get_controls_html(mic_on: bool = True, cam_on: bool = True) -> str:
    """Generate the mic/camera control bar HTML."""
    mic_bg = "#48BB78" if mic_on else "#E53E3E"
    cam_bg = "#4299e1" if cam_on else "#E53E3E"
    mic_label = "&#127908; Mic ON" if mic_on else "&#128263; Mic OFF"
    cam_label = "&#128247; Cam ON" if cam_on else "&#128247; Cam OFF"

    return f"""
    <div style="
        display: flex; justify-content: center; gap: 12px; padding: 16px;
        background: #f7fafc; border-radius: 12px; border: 1px solid #e2e8f0;
        margin-top: 12px;
    ">
        <div style="
            background: {mic_bg}; color: white;
            padding: 10px 22px; border-radius: 10px;
            font-weight: 600; font-size: 0.9rem; display: inline-block;
        ">{mic_label}</div>
        <div style="
            background: {cam_bg}; color: white;
            padding: 10px 22px; border-radius: 10px;
            font-weight: 600; font-size: 0.9rem; display: inline-block;
        ">{cam_label}</div>
        <div style="
            background: #e2e8f0; color: #4a5568;
            padding: 10px 22px; border-radius: 10px;
            font-weight: 500; font-size: 0.85rem; display: inline-block;
        ">&#9679; Recording</div>
    </div>
    """
