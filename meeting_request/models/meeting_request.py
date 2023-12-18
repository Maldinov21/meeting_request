from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import ValidationError
import qrcode
import base64
from io import BytesIO

class MeetingRequest(models.Model):
    _name = "meeting.request"
    _description = 'Meeting Request'

    partner_id = fields.Many2one('res.partner', string='Nama Rekan', default=lambda self: self.env.user.partner_id.id, required=True)
    partner_ids = fields.Many2many('res.partner', string='Peserta Meeting')
    meeting_purpose = fields.Char(string='Tujuan Meeting', required=True)
    description = fields.Char(string='Deskripsi Meeting')
    meeting_date_start = fields.Datetime(
        string='Tanggal dan Jam Mulai Meeting',
        required=True,
        default=fields.Datetime.now,
    )
    meeting_date_stop = fields.Datetime(
        string='Tanggal dan Jam Selesai Meeting',
        required=True,
        default=fields.Datetime.now,
    )
    attachment_pdf = fields.Binary(string='Attachment PDF', attachment=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft')
    qrcode_image = fields.Binary(string='QRCode Image', attachment=False, readonly=True)

    def action_submit(self):
        for record in self:
            record.write({'status': 'pending'})
            return True
    
    def action_confirm(self):
        for record in self:
            record.write({'status': 'confirm'})
            return True
    
    def generate_qrcode(self, data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=7,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = BytesIO()
        img.save(img_buffer)
        img_data = img_buffer.getvalue()

        return img_data

    def action_approve(self):
        calendar_event_obj = self.env['calendar.event']

        for record in self:
            if not record.partner_ids:
                raise ValidationError(" 'Peserta Meeting' harus diisi sebelum dapat disetujui.")

            calendar_event_data = {
                'name': record.meeting_purpose,
                'partner_ids': [(6, 0, record.partner_ids.ids)],
                'start': record.meeting_date_start,
                'stop': record.meeting_date_stop,
                'allday': False,
                'description': record.description,
            }
            calendar_event = calendar_event_obj.create(calendar_event_data)

            # Generate QRCode
            qrcode_data =f"Meeting Purpose: {record.meeting_purpose}\nMeeting Date Start: {record.meeting_date_start}\nMeeting Date Start Stop: {record.meeting_date_stop}\nMeeting Description: {record.description}"
            qrcode_image = record.generate_qrcode(qrcode_data)
            record.write({'qrcode_image': base64.b64encode(qrcode_image)})

            # Kirim email ke partner_id
            self.send_email_approve()

            # Kirim email ke setiap partner di partner_ids
            # for partner in record.partner_ids:
            #     self.send_email_approve(partner, record)

            record.write({'status': 'approve'})

        return calendar_event
    
    def send_email_approve(self):
        template = self.env.ref('meeting_request.meeting_invitation')
        for record in self:
            if record.partner_id.email:
                template.send_mail(record.id, force_send=True)
    
    def send_email_cancel(self):
        template = self.env.ref('meeting_request.meeting_cancelled')
        for record in self:
            if record.partner_id.email:
                template.send_mail(record.id, force_send=True)
    
    def action_cancel(self):
        for record in self:
            self.send_email_cancel()
            record.write({'status': 'cancel'})
            return True
    
    def set_draft(self):
        for record in self:
            record.write({'status': 'draft'})
            return True
    
    @api.constrains('meeting_date_start','meeting_date_stop')
    def _check_meeting_date(self):
        for record in self:
            if record.meeting_date_start and record.meeting_date_stop < fields.Datetime.now():
                raise ValidationError("Tanggal dan Jam Meeting tidak dapat diisi dengan waktu sebelum hari ini.")
    