# RC Monit

This is the Kiro Workshop activity as part of Research Skilling Accelerator – Week 1 Lab - Research AND Research IT.

The use case that I build is "RC Monit" – Research Computing — CloudWatch Monitoring.

See the initial [PLAN.md](rc_monit/PLAN.md) problem statement and the end solution that produces in [README.md](rc_monit/README.md)

The [_screenshots](_screenshots) capture some intermediate steps of developing with Kiro.

![rsa_week1_kiro_rc_monit_1.png](_screenshots/rsa_week1_kiro_rc_monit_1.png)

## Deploy

The workshop EC2 comes with the `docker` pre-installed. So, I use terraform image to run the commands.

Like so.

```bash
cd rc_monit
docekr pull hashicorp/terraform:latest
docker run --rm -v "$(pwd):/app" -w /app hashicorp/terraform:latest fmt -recursive
docker run --rm -v "$(pwd):/app" -w /app hashicorp/terraform:latest validate
docker run --rm -v "$(pwd):/app" -w /app hashicorp/terraform:latest plan -no-color | tee terraform-plan.txt
docker run --rm -v "$(pwd):/app" -w /app hashicorp/terraform:latest apply -no-color -auto-approve | tee terraform-apply.txt
docker run --rm -v "$(pwd):/app" -w /app hashicorp/terraform:latest destroy -no-color -auto-approve | tee terraform-destroy.txt
```
